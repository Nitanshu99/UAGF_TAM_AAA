"""Repository paths and version floor for the bootstrap."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_DIR = REPO_ROOT / ".venv"
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
REQ_DEV = REPO_ROOT / "requirements-dev.txt"
REQ_PROD = REPO_ROOT / "requirements.txt"

MIN_PY = (3, 12)
