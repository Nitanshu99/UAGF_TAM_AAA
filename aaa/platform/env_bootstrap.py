"""Helpers for loading repository environment variables early in app entrypoints."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def under_pytest() -> bool:
    """True when running under pytest — keep the test environment hermetic."""
    return "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))


_under_pytest = under_pytest


def load_repo_dotenv(repo_root: Path) -> bool:
    """Load ``repo_root/.env`` into ``os.environ`` when python-dotenv is available.

    Existing environment values always win (``override=False``), so inline/CI
    settings take precedence over ``.env``. Skipped entirely under pytest so a
    developer's ``.env`` never bleeds into the test environment.
    """
    if _under_pytest():
        return False
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - optional during bootstrap
        return False

    env_file = repo_root / ".env"
    if not env_file.exists():
        return False
    return bool(load_dotenv(env_file, override=False))
