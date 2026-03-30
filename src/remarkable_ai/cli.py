"""remarkable-ai CLI: push diagrams, fetch annotations, render SVGs, create blank pages."""

import sys
import tempfile
from pathlib import Path

import cyclopts

from remarkable_ai.remarkable import RemarkableError
from remarkable_ai.svg import SvgConversionError

app = cyclopts.App(
    name="remarkable-ai",
    help="Push diagrams to reMarkable, fetch annotated drawings, render handwritten notes.",
)

DEFAULT_FOLDER = "/AI Brainstorm/"


def handle_errors(func):  # noqa: ANN001, ANN201 — cyclopts decorator compat
    """Wrap CLI commands to catch domain errors and print cleanly."""

    def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        try:
            return func(*args, **kwargs)
        except (RemarkableError, SvgConversionError, FileNotFoundError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__
    wrapper.__module__ = func.__module__
    return wrapper


@app.command
@handle_errors
def push(
    path: Path,
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Upload a PDF or SVG to the reMarkable tablet.

    If the file is an SVG, it's converted to PDF first.
    """
    from remarkable_ai.remarkable import push as do_push
    from remarkable_ai.svg import svg_to_pdf

    if path.suffix == ".svg":
        pdf_path = svg_to_pdf(str(path))
        print(f"Converted SVG → {pdf_path}")
    else:
        pdf_path = str(path)

    do_push(pdf_path, folder)


@app.command
@handle_errors
def fetch(
    name: str,
    folder: str = DEFAULT_FOLDER,
    output: str | None = None,
) -> None:
    """Download an annotated document from the reMarkable and render annotations."""
    from remarkable_ai.remarkable import fetch as do_fetch

    result = do_fetch(name, folder, output)
    print(f"Output: {result}")


@app.command(name="list")
@handle_errors
def list_files(
    folder: str = DEFAULT_FOLDER,
) -> None:
    """List files in a reMarkable folder."""
    from remarkable_ai.remarkable import list_folder

    print(list_folder(folder))


@app.command
@handle_errors
def blank(
    title: str,
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Create a blank page with a title and push it to the reMarkable."""
    from remarkable_ai.blank import create_blank_page
    from remarkable_ai.remarkable import push as do_push

    slug = title.lower().replace(" ", "-")[:40]
    pdf_path = str(Path(tempfile.gettempdir()) / f"{slug}.pdf")
    create_blank_page(title, pdf_path)
    do_push(pdf_path, folder)


@app.command
@handle_errors
def render(
    svg_path: Path,
    pdf: bool = False,
    push_to_tablet: bool = False,
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Render an SVG to PNG (for review) or PDF, optionally push to reMarkable."""
    from remarkable_ai.remarkable import push as do_push
    from remarkable_ai.svg import svg_to_pdf, svg_to_png

    if pdf or push_to_tablet:
        result = svg_to_pdf(str(svg_path))
        print(f"PDF: {result}")
        if push_to_tablet:
            do_push(result, folder)
    else:
        result = svg_to_png(str(svg_path))
        print(f"PNG: {result}")


@app.command
@handle_errors
def calibrate(
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Push a 9-point calibration grid to the reMarkable."""
    from remarkable_ai.calibrate import create_calibration_grid
    from remarkable_ai.remarkable import push as do_push

    grid_path = create_calibration_grid()
    do_push(grid_path, folder)
    print("Circle each crosshair, sync, then run: remarkable-ai fetch calibration-grid")


def main() -> None:
    app()
