"""Generate template PDFs to push to the reMarkable.

Two templates right now:

    BLANK          A titled page with a light border.
                   For freehand drawing/explanation.

    CALIBRATION    A 9-point crosshair grid. Circle each
                   crosshair on the tablet, fetch it back,
                   and you can solve the coordinate transform.

        D:TL ───── G:TM ───── C:TR
          │          │          │
        H:LM ───── B:CTR ──── I:RM
          │          │          │
        A:BL ───── F:BM ───── E:BR

Both are 1152x936 landscape PDFs (draw.io's default export size).
Call ``create_pdf(Template.BLANK, title="...")`` and you get a path
to a temp file ready to push.
"""

import tempfile
from enum import StrEnum
from pathlib import Path

from reportlab.pdfgen import canvas

from remarkable_ai.core.constants import LANDSCAPE_HEIGHT, LANDSCAPE_WIDTH

EDGE_MARGIN = 100
CROSSHAIR_ARM_LENGTH = 20
CIRCLE_RADIUS = 15


class Template(StrEnum):
    """Available PDF templates for the reMarkable tablet."""

    BLANK = "blank"
    CALIBRATION = "calibration"


def create_pdf(
    template: Template,
    *,
    title: str = "",
    filename: str | None = None,
    width: int = LANDSCAPE_WIDTH,
    height: int = LANDSCAPE_HEIGHT,
) -> Path:
    """Make a PDF from a template and return its path in /tmp.

    ``filename`` sets the temp file stem -- pass ``"neural-networks"``
    and you get ``/tmp/neural-networks.pdf``. Defaults to the template
    name (``blank.pdf`` or ``calibration.pdf``).
    """
    stem = filename or template.value
    output_path = Path(tempfile.gettempdir()) / f"{stem}.pdf"
    pdf_canvas = canvas.Canvas(str(output_path), pagesize=(width, height))

    if template == Template.BLANK:
        _draw_blank(pdf_canvas, title, width, height)
    elif template == Template.CALIBRATION:
        _draw_calibration(pdf_canvas, width, height)

    pdf_canvas.save()
    return output_path


def _draw_blank(pdf_canvas: canvas.Canvas, title: str, width: int, height: int) -> None:
    """Draw a blank page with a title and light border."""
    pdf_canvas.setFont("Helvetica-Bold", 20)
    pdf_canvas.setFillColorRGB(0.6, 0.6, 0.6)
    pdf_canvas.drawString(40, height - 40, title)
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.setFillColorRGB(0.7, 0.7, 0.7)
    pdf_canvas.drawString(40, height - 65, "Draw your explanation here")
    pdf_canvas.setStrokeColorRGB(0.85, 0.85, 0.85)
    pdf_canvas.setLineWidth(1)
    pdf_canvas.rect(20, 20, width - 40, height - 40)


def _draw_calibration(pdf_canvas: canvas.Canvas, width: int, height: int) -> None:
    """Draw a 9-point crosshair grid for coordinate calibration."""
    pdf_canvas.setFont("Helvetica-Bold", 18)
    pdf_canvas.setStrokeColorRGB(0.8, 0.2, 0.2)
    pdf_canvas.setLineWidth(2)

    crosshairs = [
        (EDGE_MARGIN, EDGE_MARGIN, "A: BL"),
        (width // 2, height // 2, "B: CENTER"),
        (width - EDGE_MARGIN, height - EDGE_MARGIN, "C: TR"),
        (EDGE_MARGIN, height - EDGE_MARGIN, "D: TL"),
        (width - EDGE_MARGIN, EDGE_MARGIN, "E: BR"),
        (width // 2, EDGE_MARGIN, "F: BM"),
        (width // 2, height - EDGE_MARGIN, "G: TM"),
        (EDGE_MARGIN, height // 2, "H: LM"),
        (width - EDGE_MARGIN, height // 2, "I: RM"),
    ]

    for center_x, center_y, label in crosshairs:
        pdf_canvas.line(
            center_x - CROSSHAIR_ARM_LENGTH,
            center_y,
            center_x + CROSSHAIR_ARM_LENGTH,
            center_y,
        )
        pdf_canvas.line(
            center_x,
            center_y - CROSSHAIR_ARM_LENGTH,
            center_x,
            center_y + CROSSHAIR_ARM_LENGTH,
        )
        pdf_canvas.circle(center_x, center_y, CIRCLE_RADIUS, stroke=1, fill=0)
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(center_x + 25, center_y + 5, label)

    pdf_canvas.setFont("Helvetica-Bold", 20)
    pdf_canvas.drawCentredString(width // 2, height // 2 + 40, "CIRCLE EACH CROSSHAIR")
    pdf_canvas.setFont("Helvetica", 14)
    instruction = "then sync and run: remarkable-ai fetch calibration-grid"
    pdf_canvas.drawCentredString(width // 2, height // 2 + 15, instruction)
