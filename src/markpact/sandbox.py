"""Sandbox management"""

import os
import socket
from pathlib import Path


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + max_attempts}")


class Sandbox:
    """Manages sandbox directory for markpact execution"""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or os.environ.get("MARKPACT_SANDBOX", "./sandbox")).resolve()
        self.path.mkdir(parents=True, exist_ok=True)

    @property
    def venv_bin(self) -> Path:
        return self.path / ".venv" / "bin"

    @property
    def venv_pip(self) -> Path:
        return self.venv_bin / "pip"

    @property
    def venv_python(self) -> Path:
        return self.venv_bin / "python"

    def has_venv(self) -> bool:
        return self.venv_python.exists()

    def write_file(self, rel_path: str, content: str) -> Path:
        """Write file to sandbox, creating directories as needed"""
        full = self.path / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        return full

    def write_requirements(self, deps: list[str]) -> Path:
        """Write requirements.txt"""
        req = self.path / "requirements.txt"
        req.write_text("\n".join(deps))
        return req

    def clean(self):
        """Remove sandbox directory"""
        import shutil
        if self.path.exists():
            shutil.rmtree(self.path)
