"""Calibration grid: generate a 9-point crosshair PDF for solving the coordinate transform."""

import tempfile
from pathlib import Path

from reportlab.pdfgen import canvas


def create_calibration_grid(
    output: str | None = None,
    width: int = 1152,
    height: int = 936,
) -> str:
    """Create a PDF with 9 crosshairs at known positions for coordinate calibration."""
    out = output or str(Path(tempfile.gettempdir()) / "calibration-grid.pdf")
    c = canvas.Canvas(out, pagesize=(width, height))
    c.setFont("Helvetica-Bold", 18)
    c.setStrokeColorRGB(0.8, 0.2, 0.2)
    c.setLineWidth(2)

    points = [
        (100, 100, "A: BL"),
        (width // 2, height // 2, "B: CENTER"),
        (width - 100, height - 100, "C: TR"),
        (100, height - 100, "D: TL"),
        (width - 100, 100, "E: BR"),
        (width // 2, 100, "F: BM"),
        (width // 2, height - 100, "G: TM"),
        (100, height // 2, "H: LM"),
        (width - 100, height // 2, "I: RM"),
    ]

    for x, y, label in points:
        c.line(x - 20, y, x + 20, y)
        c.line(x, y - 20, x, y + 20)
        c.circle(x, y, 15, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x + 25, y + 5, label)

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width // 2, height // 2 + 40, "CIRCLE EACH CROSSHAIR")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width // 2, height // 2 + 15, "then sync and run: remarkable-ai fetch calibration-grid")
    c.save()
    return out
