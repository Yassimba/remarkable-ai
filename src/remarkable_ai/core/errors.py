"""Domain exceptions for remarkable-ai.

All exceptions inherit from CLIError so the CLI error handler can catch
them uniformly without importing each one individually.
"""


class CLIError(Exception):
    """Base for all remarkable-ai domain errors.

    The CLI decorator catches this type and prints the message to stderr
    instead of showing a full traceback.
    """


class RemarkableError(CLIError):
    """Raised when a reMarkable cloud operation fails (push, fetch, list)."""


class SvgConversionError(CLIError):
    """Raised when no SVG renderer is available or conversion fails."""
