"""remarkable-ai CLI: push diagrams, fetch annotations, render SVGs, create blank pages."""

from pathlib import Path

import cyclopts

app = cyclopts.App(
    name="remarkable-ai",
    help="Push diagrams to reMarkable, fetch annotated drawings, render handwritten notes.",
)

DEFAULT_FOLDER = "/AI Brainstorm/"


@app.command
def push(
    path: Path,
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Upload a PDF or SVG to the reMarkable tablet.

    If the file is an SVG, it's converted to PDF first.
    """
    if path.suffix == ".svg":
        from remarkable_ai.svg import svg_to_pdf

        pdf_path = svg_to_pdf(str(path))
        print(f"Converted SVG → {pdf_path}")
    else:
        pdf_path = str(path)

    from remarkable_ai.remarkable import push as do_push

    do_push(pdf_path, folder)


@app.command
def fetch(
    name: str,
    folder: str = DEFAULT_FOLDER,
    output: str | None = None,
) -> None:
    """Download an annotated document from the reMarkable and render annotations.

    Downloads the .rmdoc, extracts handwritten strokes, renders them onto
    the original PDF with calibrated coordinate alignment, and saves the result.
    """
    from remarkable_ai.remarkable import fetch as do_fetch

    result = do_fetch(name, folder, output)
    print(f"Output: {result}")


@app.command(name="list")
def list_files(
    folder: str = DEFAULT_FOLDER,
) -> None:
    """List files in a reMarkable folder."""
    from remarkable_ai.remarkable import list_folder

    print(list_folder(folder))


@app.command
def blank(
    title: str,
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Create a blank page with a title and push it to the reMarkable.

    Use this to set up a drawing surface before sketching an explanation.
    """
    from remarkable_ai.blank import create_blank_page
    from remarkable_ai.remarkable import push as do_push

    slug = title.lower().replace(" ", "-")[:40]
    pdf_path = f"/tmp/{slug}.pdf"
    create_blank_page(title, pdf_path)
    do_push(pdf_path, folder)


@app.command
def render(
    svg_path: Path,
    pdf: bool = False,
    push_to_tablet: bool = False,
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Render an SVG to PNG (for review) or PDF, optionally push to reMarkable.

    Without --pdf, renders to PNG for visual inspection.
    With --pdf, converts to PDF.
    With --push-to-tablet, also uploads the PDF to the reMarkable.
    """
    if pdf or push_to_tablet:
        from remarkable_ai.svg import svg_to_pdf

        result = svg_to_pdf(str(svg_path))
        print(f"PDF: {result}")
        if push_to_tablet:
            from remarkable_ai.remarkable import push as do_push

            do_push(result, folder)
    else:
        from remarkable_ai.svg import svg_to_png

        result = svg_to_png(str(svg_path))
        print(f"PNG: {result}")


@app.command
def calibrate(
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Push a 9-point calibration grid to the reMarkable.

    Circle each crosshair on the tablet, sync, then run:
        remarkable-ai fetch calibration-grid
    to verify alignment.
    """
    from remarkable_ai.calibrate import create_calibration_grid
    from remarkable_ai.remarkable import push as do_push

    grid_path = create_calibration_grid()
    do_push(grid_path, folder)
    print("Circle each crosshair, sync, then run: remarkable-ai fetch calibration-grid")


def main() -> None:
    app()
