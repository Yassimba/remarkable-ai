"""Convert SVG files to PNG or PDF.

Tries three backends in order::

    rsvg-convert  ──▶  cairosvg  ──▶  Inkscape
    (C, ~50ms)         (Python)       (full editor, ~2s)
       │                  │               │
       ▼                  ▼               ▼
    fastest            no binary       last resort
    install:           needed,         but handles
    brew install       pip install     weird SVGs
    librsvg            cairosvg

If all three fail, raises SvgConversionError with what went wrong for
each backend and an install hint.

The main entry point is ``convert_svg(path, format)``. The old
``svg_to_png`` / ``svg_to_pdf`` functions are thin wrappers around it.
"""

import subprocess
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path

from remarkable_ai.core.errors import SvgConversionError

type Converter = tuple[str, Callable[[], None]]

CONVERSION_TIMEOUT_SECONDS = 30


class OutputFormat(StrEnum):
    """Target format for SVG conversion."""

    PNG = "png"
    PDF = "pdf"


def convert_svg(
    svg_path: Path, output_format: OutputFormat = OutputFormat.PDF, output_path: Path | None = None, dpi: int = 150
) -> Path:
    """Convert an SVG to PNG or PDF.

    Tries rsvg, cairosvg, then Inkscape. Returns the output path.
    dpi only matters for PNG (PDFs are vector).
    """
    target = output_path or svg_path.with_suffix(f".{output_format.value}")
    source = str(svg_path)
    target_str = str(target)
    converters = build_converter_chain(source, target_str, output_format, dpi)
    try_converters(converters)
    return target


def svg_to_png(svg_path: Path, output: Path | None = None, dpi: int = 150) -> Path:
    """Convert an SVG file to PNG. Thin alias for ``convert_svg``."""
    return convert_svg(svg_path, OutputFormat.PNG, output, dpi)


def svg_to_pdf(svg_path: Path, output: Path | None = None) -> Path:
    """Convert an SVG file to PDF. Thin alias for ``convert_svg``."""
    return convert_svg(svg_path, OutputFormat.PDF, output)


def build_converter_chain(source: str, target: str, output_format: OutputFormat, dpi: int) -> list[Converter]:
    """Build the prioritized converter list for the given output format."""
    if output_format == OutputFormat.PNG:
        return [
            (
                "rsvg-convert",
                lambda: _run_cli(["rsvg-convert", "-o", target, f"--dpi-x={dpi}", f"--dpi-y={dpi}", source]),
            ),
            ("cairosvg", lambda: cairosvg_convert(source, target, to_pdf=False, dpi=dpi)),
            (
                "inkscape",
                lambda: _run_cli(
                    ["inkscape", source, "--export-type=png", f"--export-filename={target}", f"--export-dpi={dpi}"],
                ),
            ),
        ]
    return [
        ("rsvg-convert", lambda: _run_cli(["rsvg-convert", "-f", "pdf", "-o", target, source])),
        ("cairosvg", lambda: cairosvg_convert(source, target, to_pdf=True)),
        ("inkscape", lambda: _run_cli(["inkscape", source, "--export-type=pdf", f"--export-filename={target}"])),
    ]


def try_converters(converters: list[Converter]) -> None:
    """Try each converter in priority order until one succeeds."""
    errors: list[str] = []
    for name, converter in converters:
        try:
            converter()
        except (FileNotFoundError, ImportError, subprocess.CalledProcessError) as exc:
            errors.append(f"  {name}: {exc}")
        else:
            return
    raise SvgConversionError(
        "No SVG renderer found. Tried:\n" + "\n".join(errors) + "\nInstall: brew install librsvg",
    )


def _run_cli(args: list[str]) -> None:
    """Run an external converter command with a timeout."""
    subprocess.run(args, capture_output=True, check=True, timeout=CONVERSION_TIMEOUT_SECONDS)


def cairosvg_convert(source: str, target: str, *, to_pdf: bool, dpi: int = 150) -> None:
    """Convert via cairosvg (lazy-imported to avoid hard dependency)."""
    import cairosvg

    if to_pdf:
        cairosvg.svg2pdf(url=source, write_to=target)
    else:
        cairosvg.svg2png(url=source, write_to=target, dpi=dpi)
