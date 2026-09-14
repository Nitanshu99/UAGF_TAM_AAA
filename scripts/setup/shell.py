"""Subprocess and .env helpers for the bootstrap."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts.setup.console import err
from scripts.setup.paths import REPO_ROOT, VENV_DIR


def run(cmd: list[str], cwd: Path | None = None, check: bool = True,
        env: dict[str, str] | None = None) -> int:
    """Echo and run *cmd*; exit(1) on failure when *check* is set.

    :param cmd: Command and arguments.
    :param cwd: Working directory (defaults to the repo root).
    :param check: Exit the process when the command fails.
    :param env: Optional environment override.
    :returns: The command's return code.
    """
    print(f"  $ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd or REPO_ROOT), env=env, check=False)
    if check and proc.returncode != 0:
        err(f"command failed (exit {proc.returncode}): {' '.join(cmd)}")
        sys.exit(1)
    return proc.returncode


def load_dotenv(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict (no shell expansion, no exports)."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.split("#", 1)[0].strip().strip('"').strip("'")
        out[key.strip()] = val
    return out


def venv_bin(name: str) -> Path:
    """Return the path to ``name`` inside ``.venv/`` (Windows-aware)."""
    sub = "Scripts" if os.name == "nt" else "bin"
    return VENV_DIR / sub / name
