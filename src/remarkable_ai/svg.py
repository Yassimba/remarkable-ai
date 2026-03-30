"""SVG rendering: convert SVG to PNG (for review) or PDF (for reMarkable)."""

import subprocess
import sys
from pathlib import Path


def svg_to_png(svg_path: str, output: str | None = None, dpi: int = 150) -> str:
    """Convert SVG to PNG. Tries rsvg-convert, cairosvg, then inkscape."""
    out = output or svg_path.replace(".svg", ".png")

    for converter in [
        lambda: subprocess.run(
            ["rsvg-convert", "-o", out, f"--dpi-x={dpi}", f"--dpi-y={dpi}", svg_path],
            capture_output=True,
            check=True,
        ),
        lambda: __import__("cairosvg").svg2png(url=svg_path, write_to=out, dpi=dpi),
        lambda: subprocess.run(
            ["inkscape", svg_path, "--export-type=png", f"--export-filename={out}", f"--export-dpi={dpi}"],
            capture_output=True,
            check=True,
        ),
    ]:
        try:
            converter()
            return out
        except (FileNotFoundError, ImportError, subprocess.CalledProcessError):
            continue

    print("No SVG renderer found. Install: brew install librsvg", file=sys.stderr)
    sys.exit(1)


def svg_to_pdf(svg_path: str, output: str | None = None) -> str:
    """Convert SVG to PDF. Tries rsvg-convert, cairosvg, then inkscape."""
    out = output or svg_path.replace(".svg", ".pdf")

    for converter in [
        lambda: subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", out, svg_path],
            capture_output=True,
            check=True,
        ),
        lambda: __import__("cairosvg").svg2pdf(url=svg_path, write_to=out),
        lambda: subprocess.run(
            ["inkscape", svg_path, "--export-type=pdf", f"--export-filename={out}"],
            capture_output=True,
            check=True,
        ),
    ]:
        try:
            converter()
            return out
        except (FileNotFoundError, ImportError, subprocess.CalledProcessError):
            continue

    print("No SVG→PDF converter found. Install: brew install librsvg", file=sys.stderr)
    sys.exit(1)
