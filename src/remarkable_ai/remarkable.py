"""Core logic: interact with reMarkable cloud via the remark CLI."""

import subprocess
from pathlib import Path

from remarkable_ai.renderer import extract_strokes, render_annotations


class RemarkableError(Exception):
    """Raised when a remark CLI command fails."""


def run_remark(args: list[str]) -> str:
    """Execute a remark CLI command and return stdout."""
    result = subprocess.run(["remark", *args], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RemarkableError(result.stderr.strip())
    return result.stdout


def push(pdf_path: str, folder: str) -> None:
    """Upload a PDF to the reMarkable tablet."""
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    run_remark(["put", pdf_path, folder])
    name = Path(pdf_path).stem
    print(f"Pushed '{name}' to {folder}")


def fetch(name: str, folder: str, output: str | None = None) -> str:
    """Download an annotated document, render annotations, return output path."""
    remote = f"{folder}{name}"
    run_remark(["get", remote])

    rmdoc = Path(f"{name}.rmdoc")
    if not rmdoc.exists():
        rmdoc = Path(f"{name}.zip")
    if not rmdoc.exists():
        raise FileNotFoundError(f"Download failed — no {name}.rmdoc found")

    strokes, pdf_path = extract_strokes(rmdoc)
    output_path = output or f"/tmp/{name}-annotated.pdf"
    render_annotations(strokes, pdf_path, output_path)

    rmdoc.unlink(missing_ok=True)
    Path(f"{name}.zip").unlink(missing_ok=True)

    return output_path


def list_folder(folder: str) -> str:
    """List contents of a reMarkable folder."""
    return run_remark(["ls", folder])
