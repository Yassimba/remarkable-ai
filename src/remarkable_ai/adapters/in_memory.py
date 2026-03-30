"""Fake transport for tests -- a dict pretending to be the cloud.

Seed it with .rmdoc fixtures via ``seed_document()``, then run the
full fetch pipeline against it. Check ``upload_log`` to assert what
got pushed. No subprocess, no network, no tablet needed.
"""

from pathlib import Path

from remarkable_ai.core.errors import RemarkableError
from remarkable_ai.core.transport import CloudTransport


class InMemoryAdapter(CloudTransport):
    """Fake transport for testing the full pipeline without a tablet."""

    def __init__(self) -> None:
        """Initialize empty storage and upload log."""
        self.files: dict[tuple[str, str], Path] = {}
        self.upload_log: list[tuple[Path, str]] = []

    def upload(self, local_path: Path, remote_folder: str) -> None:
        """Record the upload for later assertion."""
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")
        self.files[(remote_folder, local_path.stem)] = local_path
        self.upload_log.append((local_path, remote_folder))

    def download(self, document_name: str, remote_folder: str) -> Path:
        """Return a previously seeded document path."""
        key = (remote_folder, document_name)
        if key not in self.files:
            raise RemarkableError(f"Document '{document_name}' not found in {remote_folder}")
        return self.files[key]

    def list_folder(self, remote_folder: str) -> str:
        """List seeded documents in the given folder."""
        matching = [name for (folder, name) in self.files if folder == remote_folder]
        if not matching:
            return "(empty)"
        return "\n".join(sorted(matching))

    def seed_document(self, document_name: str, remote_folder: str, archive_path: Path) -> None:
        """Pre-populate a document so ``download`` can find it."""
        self.files[(remote_folder, document_name)] = archive_path
