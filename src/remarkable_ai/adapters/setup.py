"""Download and install the ``remark`` (rmapi) binary.

Grabs the right pre-built binary from GitHub for this platform,
drops it in ~/.local/bin as ``remark``. No Go toolchain needed.

    remarkable-ai setup
        │
        ├── detect platform (darwin-arm64, linux-amd64, etc.)
        ├── curl the .zip/.tar.gz from ddvk/rmapi releases
        ├── extract → copy to ~/.local/bin/remark
        └── run ``remark`` once for cloud auth
"""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from remarkable_ai.core.errors import CLIError

RMAPI_REPO = "ddvk/rmapi"
INSTALL_DIR_DEFAULT = Path.home() / ".local" / "bin"

# (system, machine) → GitHub release asset name.
# machine aliases (aarch64/arm64, x86_64/amd64) are both listed.
PLATFORM_ASSETS: dict[tuple[str, str], str] = {
    ("darwin", "arm64"): "rmapi-macos-arm64.zip",
    ("darwin", "x86_64"): "rmapi-macos-intel.zip",
    ("linux", "x86_64"): "rmapi-linux-amd64.tar.gz",
    ("linux", "amd64"): "rmapi-linux-amd64.tar.gz",
    ("linux", "aarch64"): "rmapi-linux-arm64.tar.gz",
    ("linux", "arm64"): "rmapi-linux-arm64.tar.gz",
    ("windows", "x86_64"): "rmapi-win64.zip",
    ("windows", "amd64"): "rmapi-win64.zip",
    ("windows", "arm64"): "rmapi-win-arm64.zip",
    ("windows", "aarch64"): "rmapi-win-arm64.zip",
}


def _detect_asset_name() -> str:
    """Pick the right rmapi release asset for this machine."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    key = (system, machine)

    if key not in PLATFORM_ASSETS:
        raise CLIError(f"Unsupported platform: {system} {machine}")
    return PLATFORM_ASSETS[key]


def _find_binary(extract_dir: Path) -> Path:
    """Find the rmapi binary inside an extracted archive."""
    for candidate in extract_dir.rglob("rmapi*"):
        if candidate.is_file():
            return candidate
    raise CLIError(f"No rmapi binary found in {extract_dir}")


def install_remark(install_dir: Path = INSTALL_DIR_DEFAULT) -> Path:
    """Download and install the remark binary. Returns the installed path."""
    asset_name = _detect_asset_name()
    download_url = f"https://github.com/{RMAPI_REPO}/releases/latest/download/{asset_name}"

    with tempfile.TemporaryDirectory(prefix="rmapi-") as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / asset_name

        subprocess.run(
            ["curl", "-fSL", "-o", str(archive_path), download_url],
            check=True,
            timeout=120,
        )

        shutil.unpack_archive(archive_path, temp_path)
        binary_path = _find_binary(temp_path)

        install_dir.mkdir(parents=True, exist_ok=True)
        target_name = "remark.exe" if platform.system().lower() == "windows" else "remark"
        target_path = install_dir / target_name
        shutil.copy2(binary_path, target_path)
        target_path.chmod(target_path.stat().st_mode | 0o111)

    return target_path


def is_on_path(install_dir: Path = INSTALL_DIR_DEFAULT) -> bool:
    """Check if install_dir is on PATH."""
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    return str(install_dir) in path_dirs


def run_auth() -> None:
    """Run ``remark`` interactively so the user can authenticate."""
    remark_path = shutil.which("remark")
    if not remark_path:
        raise CLIError("remark binary not found on PATH after install")
    subprocess.run([remark_path], check=False)
