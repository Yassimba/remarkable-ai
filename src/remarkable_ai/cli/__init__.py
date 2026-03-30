"""The ``remarkable-ai`` CLI entry point.

Commands live in ``commands.py`` and register themselves on the ``app``
when ``main()`` imports them. Everything else (adapters, reportlab,
rmscene) is lazy-imported inside each command so ``--help`` stays fast.
"""

import sys
from collections.abc import Callable
from functools import wraps

import cyclopts
from rich.console import Console

from remarkable_ai.core.errors import CLIError

app = cyclopts.App(
    name="remarkable-ai",
    help="Push diagrams to reMarkable, fetch annotated drawings, render handwritten notes.",
)

console = Console()
error_console = Console(stderr=True)

DEFAULT_FOLDER = "/AI Brainstorm/"

type Command = Callable[..., None]


def handle_errors(func: Command) -> Command:
    """Catch CLIError and FileNotFoundError, print to stderr, exit 1."""

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> None:
        try:
            func(*args, **kwargs)
        except (CLIError, FileNotFoundError) as exc:
            error_console.print(f"[bold red]Error:[/bold red] {exc}")
            sys.exit(1)

    return wrapper


def main() -> None:
    """Entry point for the remarkable-ai CLI."""
    import remarkable_ai.cli.commands  # noqa: F401

    app()
