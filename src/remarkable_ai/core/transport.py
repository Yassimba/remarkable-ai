"""The transport port -- what the CLI needs from a reMarkable backend.

Two implementations exist: RemarkCLIAdapter (production, shells out to
the ``remark`` binary) and InMemoryAdapter (tests, no network). The
port only moves files around. Parsing .rmdoc archives and rendering
strokes happen outside this boundary.

    ┌─────────────────────────────────────────────────┐
    │  CLI commands                                   │
    │     push()  fetch()  list()                     │
    └──────────┬──────────────────────────────────────┘
               │ calls
    ┌──────────▼──────────────────────────────────────┐
    │  CloudTransport  (this file -- the port)        │
    │     upload()  download()  list_folder()         │
    └──────────┬──────────────────────────────────────┘
               │ implemented by
    ┌──────────▼──────────┐  ┌────────────────────────┐
    │  RemarkCLIAdapter   │  │  InMemoryAdapter       │
    │  (subprocess)       │  │  (dict, for tests)     │
    └─────────────────────┘  └────────────────────────┘
"""

from abc import ABC, abstractmethod
from pathlib import Path


class CloudTransport(ABC):
    """Three operations: upload a file, download an archive, list a folder.

    Each maps to one network call. Implementations raise RemarkableError
    on failure and FileNotFoundError when a file is missing.
    """

    @abstractmethod
    def upload(self, local_path: Path, remote_folder: str) -> None:
        """Send a local file to the tablet."""

    @abstractmethod
    def download(self, document_name: str, remote_folder: str) -> Path:
        """Pull a .rmdoc/.zip archive to disk. Caller cleans up the file."""

    @abstractmethod
    def list_folder(self, remote_folder: str) -> str:
        """Get a folder listing as plain text."""
