"""CLI commands: setup, push, fetch, list, blank, render, calibrate."""

import re
import shutil
import tempfile
from pathlib import Path

from remarkable_ai.adapters.remark_cli import RemarkCLIAdapter
from remarkable_ai.adapters.renderer import extract_strokes, render_annotations
from remarkable_ai.adapters.setup import install_remark, is_on_path, run_auth
from remarkable_ai.adapters.svg import svg_to_pdf, svg_to_png
from remarkable_ai.adapters.templates import Template, create_pdf
from remarkable_ai.cli import DEFAULT_FOLDER, app, console, handle_errors


@app.command
@handle_errors
def setup() -> None:
    """Download the remark binary and authenticate with reMarkable cloud.

    Run this once before using any other command. Downloads the right
    binary for your platform — no Go toolchain needed.
    """
    if not shutil.which("remark"):
        console.print("Downloading remark binary...")
        target = install_remark()
        console.print(f"Installed to [bold]{target}[/bold]")
        if not is_on_path(target.parent):
            console.print(f"[yellow]Add {target.parent} to your PATH:[/yellow]")
            console.print(f'  export PATH="{target.parent}:$PATH"')
            return

    console.print("Authenticating with reMarkable cloud...")
    run_auth()
    console.print("[green]Setup complete.[/green]")


@app.command
@handle_errors
def push(path: Path, folder: str = DEFAULT_FOLDER) -> None:
    """Upload a PDF or SVG to the reMarkable tablet.

    SVG files are automatically converted to PDF before upload.
    """
    transport = RemarkCLIAdapter()

    upload_path = path
    if path.suffix == ".svg":
        upload_path = svg_to_pdf(path)
        console.print(f"Converted SVG -> {upload_path}")

    transport.upload(upload_path, folder)
    console.print(f"Pushed [bold]'{upload_path.stem}'[/bold] to {folder}")


@app.command
@handle_errors
def fetch(
    name: str,
    folder: str = DEFAULT_FOLDER,
    output: Path | None = None,
) -> None:
    """Download an annotated document and render strokes onto the PDF."""
    transport = RemarkCLIAdapter()
    archive_path = transport.download(name, folder)
    try:
        strokes, source_pdf = extract_strokes(archive_path)
    finally:
        archive_path.unlink(missing_ok=True)

    output_path = output or Path(tempfile.gettempdir()) / f"{name}-annotated.pdf"
    stroke_count = render_annotations(strokes, source_pdf, output_path)
    console.print(f"Rendered [bold]{stroke_count}[/bold] strokes -> {output_path}")


@app.command(name="list")
@handle_errors
def list_files(
    folder: str = DEFAULT_FOLDER,
) -> None:
    """List files in a reMarkable folder."""
    transport = RemarkCLIAdapter()
    console.print(transport.list_folder(folder))


@app.command
@handle_errors
def blank(title: str, folder: str = DEFAULT_FOLDER) -> None:
    """Create a blank drawing page and push it to the reMarkable."""
    transport = RemarkCLIAdapter()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "blank"
    pdf_path = create_pdf(Template.BLANK, title=title, filename=slug)
    transport.upload(pdf_path, folder)
    console.print(f"Pushed [bold]'{slug}'[/bold] to {folder}")


@app.command
@handle_errors
def render(svg_path: Path, pdf: bool = False, push_to_tablet: bool = False, folder: str = DEFAULT_FOLDER) -> None:
    """Render an SVG to PNG (for review) or PDF (for reMarkable).

    Use --pdf to produce a PDF instead of PNG. Add --push-to-tablet to
    upload the PDF to the reMarkable in one step.
    """
    if not (pdf or push_to_tablet):
        result = svg_to_png(svg_path)
        console.print(f"PNG: {result}")
        return

    result = svg_to_pdf(svg_path)
    console.print(f"PDF: {result}")
    if not push_to_tablet:
        return

    transport = RemarkCLIAdapter()
    transport.upload(result, folder)
    console.print(f"Pushed [bold]'{result.stem}'[/bold] to {folder}")


@app.command
@handle_errors
def calibrate(
    folder: str = DEFAULT_FOLDER,
) -> None:
    """Push a 9-point crosshair grid to the reMarkable for coordinate calibration.

    Circle each crosshair on the tablet, sync, then run
    ``remarkable-ai fetch calibration-grid`` to solve the transform.
    """
    transport = RemarkCLIAdapter()
    grid_path = create_pdf(Template.CALIBRATION)
    transport.upload(grid_path, folder)
    console.print(f"Pushed calibration grid to {folder}")
    console.print("Circle each crosshair, sync, then run: [bold]remarkable-ai fetch calibration-grid[/bold]")
