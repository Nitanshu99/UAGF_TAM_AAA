"""Bootstrap steps 1–4: Python check, venv, dependencies, .env."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from scripts.setup.console import err, ok, warn
from scripts.setup.paths import (
    ENV_EXAMPLE,
    ENV_FILE,
    MIN_PY,
    REPO_ROOT,
    REQ_DEV,
    REQ_PROD,
    VENV_DIR,
)
from scripts.setup.shell import run, venv_bin


def check_python() -> None:
    """Exit unless the invoking interpreter satisfies :data:`MIN_PY`."""
    if sys.version_info < MIN_PY:
        err(f"Python {MIN_PY[0]}.{MIN_PY[1]}+ required; "
            f"this interpreter is {sys.version.split()[0]}. "
            f"Re-run with: python3.12 -m scripts.setup")
        sys.exit(1)
    ok(f"Python {sys.version.split()[0]} (>= {MIN_PY[0]}.{MIN_PY[1]})")


def create_venv(skip: bool) -> Path:
    """Create ``.venv/`` (idempotent); return the venv's python path."""
    if skip:
        warn("--no-venv: reusing current interpreter")
        return Path(sys.executable)
    if VENV_DIR.exists():
        ok(f"virtualenv already present at {VENV_DIR.relative_to(REPO_ROOT)}/")
    else:
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        ok(f"created {VENV_DIR.relative_to(REPO_ROOT)}/")
    return venv_bin("python")


def install_requirements(py: Path, with_prod: bool) -> None:
    """Upgrade pip and install the requirements file into the venv."""
    req = REQ_PROD if with_prod else REQ_DEV
    if not req.exists():
        err(f"requirements file missing: {req}")
        sys.exit(1)
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "-r", str(req)])
    ok(f"installed {req.name}")


def copy_env() -> None:
    """Copy ``.env.example`` → ``.env`` when ``.env`` is missing."""
    if ENV_FILE.exists():
        ok(".env already present")
        return
    if not ENV_EXAMPLE.exists():
        warn(".env.example missing — skipping")
        return
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    ok("created .env from .env.example (edit it before running with real secrets)")
