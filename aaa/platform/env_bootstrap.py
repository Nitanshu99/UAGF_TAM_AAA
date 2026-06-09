"""Helpers for loading repository environment variables early in app entrypoints."""
from __future__ import annotations

from pathlib import Path


def load_repo_dotenv(repo_root: Path) -> bool:
    """Load ``repo_root/.env`` into ``os.environ`` when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - optional during bootstrap
        return False

    env_file = repo_root / ".env"
    if not env_file.exists():
        return False
    return bool(load_dotenv(env_file, override=False))
