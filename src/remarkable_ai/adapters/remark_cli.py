"""Talk to the reMarkable cloud by shelling out to the ``remark`` CLI.

The ``remark`` binary (Go, separate install) handles auth and the
cloud API. We just call ``remark put``, ``remark get``, ``remark ls``
and parse the results. Each call has a 30-second timeout.
"""

import subprocess
from pathlib import Path

from remarkable_ai.core.errors import RemarkableError
from remarkable_ai.core.transport import CloudTransport

REMARK_TIMEOUT_SECONDS = 30


class RemarkCLIAdapter(CloudTransport):
    """Transport backed by the ``remark`` CLI binary."""

    def _run(self, args: list[str]) -> str:
        """Execute a remark CLI command and return stdout."""
        result = subprocess.run(
            ["remark", *args], capture_output=True, text=True, timeout=REMARK_TIMEOUT_SECONDS, check=False
        )
        if result.returncode != 0:
            raise RemarkableError(result.stderr.strip())
        return result.stdout

    def upload(self, local_path: Path, remote_folder: str) -> None:
        """Upload a file via ``remark put``."""
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")
        self._run(["put", str(local_path), remote_folder])

    def download(self, document_name: str, remote_folder: str) -> Path:
        """Pull a document via ``remark get``. Looks for .rmdoc first, .zip second."""
        remote_path = f"{remote_folder}{document_name}"
        self._run(["get", remote_path])

        candidates = [Path(f"{document_name}.rmdoc"), Path(f"{document_name}.zip")]
        archive_path = next(
            (candidate for candidate in candidates if candidate.exists()),
            None,
        )
        if not archive_path:
            raise FileNotFoundError(f"Download failed -- no {document_name}.rmdoc or .zip found")
        return archive_path

    def list_folder(self, remote_folder: str) -> str:
        """List folder contents via ``remark ls``."""
        return self._run(["ls", remote_folder])
