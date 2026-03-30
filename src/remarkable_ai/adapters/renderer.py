"""Turn reMarkable handwriting into PDF overlays.

The tablet saves pen strokes in a proprietary .rm binary format, packed
inside a .rmdoc ZIP alongside the original PDF. This module cracks that
open and draws the strokes back onto the PDF.

The pipeline has three stages::

    .rmdoc archive          .rm binary             annotated PDF
    ┌────────────┐     ┌──────────────┐     ┌───────────────────┐
    │ diagram.pdf│     │ SceneLineItem│     │ original PDF      │
    │ *.rm files │────▶│  → Stroke[]  │────▶│ + stroke overlay  │
    └────────────┘     └──────────────┘     └───────────────────┘
      extract_strokes    parse_strokes        render_annotations
                         _from_rm

Each stroke's coordinates are in tablet space (0-20967). The
CalibrationTransform maps them to the right spot on the PDF.
"""

import shutil
import tempfile
from io import BytesIO
from pathlib import Path

import rmscene
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from remarkable_ai.core.errors import RemarkableError
from remarkable_ai.core.types import CalibrationTransform, PenColor, Point, Stroke

# Calibrated 2026-03-30 from a 9-point grid on a reMarkable 2 (portrait
# mode, viewing a 1152x936 landscape PDF exported from draw.io).
DEFAULT_TRANSFORM = CalibrationTransform(scale_x=0.317575, offset_x=574.91, scale_y=-0.316282, offset_y=934.48)

PEN_COLORS_RGB: dict[PenColor, tuple[float, float, float]] = {
    PenColor.BLACK: (0.05, 0.05, 0.05),
    PenColor.GRAY: (0.5, 0.5, 0.5),
    PenColor.BLUE: (0.0, 0.15, 0.85),
    PenColor.RED: (0.9, 0.1, 0.0),
}

DEFAULT_COLOR_RGB = (0.05, 0.05, 0.05)

# Minimum rendered stroke width in PDF points (prevents invisible hairlines).
MIN_STROKE_WIDTH = 0.3

# Empirical factor that maps reMarkable pen pressure to visually-matching
# PDF stroke widths. Derived by comparing tablet output to rendered PDFs.
PRESSURE_SCALE = 0.15


def _parse_block(block: rmscene.SceneLineItemBlock) -> Stroke | None:
    try:
        value = block.item.value
    except (AttributeError, TypeError):
        return None
    if not value.points:
        return None
    color_value = value.color.value if value.color else PenColor.BLACK
    points = [Point(x=pt.x, y=pt.y, width=pt.width) for pt in value.points]
    return Stroke(points=points, color=PenColor(color_value))


def parse_strokes_from_rm(rm_path: Path) -> list[Stroke]:
    """Read a .rm binary and pull out the pen strokes.

    The .rm format has many block types (text, shapes, images) -- we only
    care about SceneLineItemBlock, which holds actual drawing data.
    Malformed blocks are silently skipped; they're rare but real.
    """
    with rm_path.open("rb") as rm_file:
        blocks = rmscene.read_blocks(rm_file)
    line_blocks = (block for block in blocks if isinstance(block, rmscene.SceneLineItemBlock))
    return [stroke for block in line_blocks if (stroke := _parse_block(block))]


def extract_strokes(rmdoc_path: Path) -> tuple[list[Stroke], Path]:
    """Unzip an .rmdoc, parse the strokes, copy out the original PDF.

    Returns (strokes, pdf_path). The PDF is copied to /tmp so we can
    delete the extraction directory. Caller should clean up the .rmdoc
    archive when done; the temp PDF sticks around for render_annotations.
    """
    extract_dir = Path(tempfile.mkdtemp(prefix="rm-"))
    try:
        shutil.unpack_archive(rmdoc_path, extract_dir)
    except (shutil.ReadError, ValueError) as exc:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise RemarkableError(f"Failed to extract {rmdoc_path}: {exc}") from exc

    rm_files = list(extract_dir.rglob("*.rm"))
    pdf_files = list(extract_dir.glob("*.pdf"))

    if not rm_files:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise RemarkableError("No annotation data found -- did you draw on the document?")
    if not pdf_files:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise RemarkableError("No PDF found in rmdoc archive")

    strokes = parse_strokes_from_rm(rm_files[0])

    stable_pdf = Path(tempfile.gettempdir()) / pdf_files[0].name
    shutil.copy2(pdf_files[0], stable_pdf)
    shutil.rmtree(extract_dir, ignore_errors=True)

    return strokes, stable_pdf


def render_annotations(
    strokes: list[Stroke], pdf_path: Path, output_path: Path, transform: CalibrationTransform = DEFAULT_TRANSFORM
) -> int:
    """Draw the strokes onto page 1 of the original PDF.

    Creates a transparent overlay with reportlab, draws each stroke as
    a colored path, then merges the overlay onto the source page with
    pypdf. Returns the stroke count.

        ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
        │ source PDF  │ + │ transparent │ = │ output PDF  │
        │ (diagram)   │   │ overlay     │   │ (annotated) │
        │             │   │  / strokes  │   │  / strokes  │
        └─────────────┘   └─────────────┘   └─────────────┘
    """
    reader = PdfReader(str(pdf_path))
    if not reader.pages:
        raise RemarkableError(f"PDF has no pages: {pdf_path}")

    page = reader.pages[0]
    pdf_width = float(page.mediabox.width)
    pdf_height = float(page.mediabox.height)

    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=(pdf_width, pdf_height))

    for stroke in strokes:
        if len(stroke.points) < 2:
            continue

        red, green, blue = PEN_COLORS_RGB.get(stroke.color, DEFAULT_COLOR_RGB)
        pdf_canvas.setStrokeColorRGB(red, green, blue)

        line_width = max(MIN_STROKE_WIDTH, stroke.points[0].width * abs(transform.scale_x) * PRESSURE_SCALE)
        pdf_canvas.setLineWidth(line_width)

        draw_path = pdf_canvas.beginPath()
        start_x, start_y = transform.to_pdf(stroke.points[0].x, stroke.points[0].y)
        draw_path.moveTo(start_x, start_y)
        for point in stroke.points[1:]:
            point_x, point_y = transform.to_pdf(point.x, point.y)
            draw_path.lineTo(point_x, point_y)
        pdf_canvas.drawPath(draw_path, stroke=1, fill=0)

    pdf_canvas.save()
    buffer.seek(0)

    overlay = PdfReader(buffer)
    page.merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    with Path(output_path).open("wb") as output_file:
        writer.write(output_file)

    return len(strokes)
