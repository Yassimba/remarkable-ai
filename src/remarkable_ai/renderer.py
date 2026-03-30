"""Parse reMarkable .rm annotation files and render them onto PDFs.

Handles coordinate transform from reMarkable's internal coordinate system
to PDF points. The transform constants are calibrated from a 9-point grid.
"""

import subprocess
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import NamedTuple

import rmscene
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


class Point(NamedTuple):
    x: float
    y: float
    width: float


class Stroke(NamedTuple):
    points: list[Point]
    color: int  # PenColor enum value


@dataclass(frozen=True, slots=True)
class CalibrationTransform:
    """Linear transform from reMarkable coordinates to PDF points.

    Solved via least-squares from a 9-point calibration grid.
    """

    scale_x: float
    offset_x: float
    scale_y: float
    offset_y: float

    def to_pdf(self, rm_x: float, rm_y: float) -> tuple[float, float]:
        return (
            self.scale_x * rm_x + self.offset_x,
            self.scale_y * rm_y + self.offset_y,
        )


# Calibrated 2026-03-30 for landscape PDFs (1152x936, draw.io default).
# reMarkable 2 in portrait mode viewing landscape PDF.
DEFAULT_TRANSFORM = CalibrationTransform(
    scale_x=0.317575,
    offset_x=574.91,
    scale_y=-0.316282,
    offset_y=934.48,
)

PEN_COLORS: dict[int, tuple[float, float, float]] = {
    0: (0.05, 0.05, 0.05),  # BLACK
    1: (0.5, 0.5, 0.5),  # GRAY
    6: (0.0, 0.15, 0.85),  # BLUE
    7: (0.9, 0.1, 0.0),  # RED
}

DEFAULT_COLOR = (0.05, 0.05, 0.05)


def parse_strokes_from_rm(rm_path: Path) -> list[Stroke]:
    """Parse .rm binary file into typed Stroke objects."""
    with open(rm_path, "rb") as f:
        blocks = list(rmscene.read_blocks(f))

    strokes: list[Stroke] = []
    for block in blocks:
        if not isinstance(block, rmscene.SceneLineItemBlock):
            continue
        item = getattr(block, "item", None)
        if item is None:
            continue
        value = getattr(item, "value", None)
        if value is None or not getattr(value, "points", None):
            continue

        color_val = getattr(getattr(value, "color", None), "value", 0)
        points = [Point(x=p.x, y=p.y, width=p.width) for p in value.points]
        strokes.append(Stroke(points=points, color=color_val))

    return strokes


def extract_strokes(rmdoc_path: Path) -> tuple[list[Stroke], Path]:
    """Extract annotation strokes and original PDF from an .rmdoc archive."""
    extract_dir = Path(tempfile.mkdtemp(prefix="rm-"))
    subprocess.run(
        ["unzip", "-o", str(rmdoc_path), "-d", str(extract_dir)],
        capture_output=True,
    )

    rm_files = list(extract_dir.rglob("*.rm"))
    pdf_files = list(extract_dir.glob("*.pdf"))

    if not rm_files:
        msg = "No annotation data found — did you draw on the document?"
        raise FileNotFoundError(msg)
    if not pdf_files:
        msg = "No PDF found in rmdoc archive"
        raise FileNotFoundError(msg)

    strokes = parse_strokes_from_rm(rm_files[0])
    return strokes, pdf_files[0]


def render_annotations(
    strokes: list[Stroke],
    pdf_path: Path,
    output_path: str,
    transform: CalibrationTransform = DEFAULT_TRANSFORM,
) -> None:
    """Render reMarkable strokes onto the original PDF."""
    reader = PdfReader(str(pdf_path))
    page = reader.pages[0]
    pdf_w = float(page.mediabox.width)
    pdf_h = float(page.mediabox.height)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(pdf_w, pdf_h))

    for stroke in strokes:
        if len(stroke.points) < 2:
            continue

        r, g, b = PEN_COLORS.get(stroke.color, DEFAULT_COLOR)
        c.setStrokeColorRGB(r, g, b)

        width = max(0.3, stroke.points[0].width * abs(transform.scale_x) * 0.15)
        c.setLineWidth(width)

        p = c.beginPath()
        x0, y0 = transform.to_pdf(stroke.points[0].x, stroke.points[0].y)
        p.moveTo(x0, y0)
        for pt in stroke.points[1:]:
            x, y = transform.to_pdf(pt.x, pt.y)
            p.lineTo(x, y)
        c.drawPath(p, stroke=1, fill=0)

    c.save()
    buf.seek(0)

    overlay = PdfReader(buf)
    page.merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Rendered {len(strokes)} strokes → {output_path}")
