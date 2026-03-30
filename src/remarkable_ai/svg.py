"""SVG rendering: convert SVG to PNG (for review) or PDF (for reMarkable)."""

import subprocess
from collections.abc import Callable
from pathlib import Path


class SvgConversionError(Exception):
    """No SVG renderer available."""


Converter = Callable[[], None]


def try_converters(converters: list[Converter]) -> None:
    """Try each converter in order until one succeeds."""
    for converter in converters:
        try:
            converter()
            return
        except (FileNotFoundError, ImportError, subprocess.CalledProcessError):
            continue
    raise SvgConversionError("No SVG renderer found. Install: brew install librsvg")


def svg_to_png(svg_path: str, output: str | None = None, dpi: int = 150) -> str:
    """Convert SVG to PNG. Tries rsvg-convert, cairosvg, then inkscape."""
    out = output or svg_path.replace(".svg", ".png")
    try_converters(
        [
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
        ]
    )
    return out


def svg_to_pdf(svg_path: str, output: str | None = None) -> str:
    """Convert SVG to PDF. Tries rsvg-convert, cairosvg, then inkscape."""
    out = output or svg_path.replace(".svg", ".pdf")
    try_converters(
        [
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
        ]
    )
    return out
