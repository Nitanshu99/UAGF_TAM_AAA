"""Locate the repository root regardless of module nesting depth."""
from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upwards from *start* until a directory with ``pyproject.toml``.

    :param start: Starting path (defaults to this file's directory).
    :returns: The repository root, or the filesystem root as a last resort.
    """
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


#: Cached repository root for path construction at import time.
REPO_ROOT: Path = find_repo_root()
