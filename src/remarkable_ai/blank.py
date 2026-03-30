"""Create blank PDF pages for user drawing on the reMarkable."""

from reportlab.pdfgen import canvas


def create_blank_page(
    title: str,
    output: str = "/tmp/blank-explain.pdf",
    width: int = 1152,
    height: int = 936,
) -> str:
    """Create a landscape PDF with a title and light border for drawing."""
    c = canvas.Canvas(output, pagesize=(width, height))
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawString(40, height - 40, title)
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.7, 0.7, 0.7)
    c.drawString(40, height - 65, "Draw your explanation here")
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setLineWidth(1)
    c.rect(20, 20, width - 40, height - 40)
    c.save()
    return output
