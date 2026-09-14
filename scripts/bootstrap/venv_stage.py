"""Stage 1 of the bootstrap: the interpreter, the virtualenv, the dependencies.

Runs under whatever ``python3.12`` the operator has — before the venv exists —
so it imports nothing outside the standard library and :mod:`scripts.setup`.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.setup.console import ok, step
from scripts.setup.paths import REPO_ROOT, VENV_DIR
from scripts.setup.shell import run
from scripts.setup.steps.env import check_python, create_venv, install_requirements

#: Files whose content decides whether the installed set is still current.
DEPENDENCY_FILES = ("requirements.txt", "requirements-dev.txt", "constraints.txt",
                    "pyproject.toml")
#: Where the fingerprint of the last successful install is kept.
FINGERPRINT = VENV_DIR / ".deps-fingerprint"


def dependency_fingerprint(root: Path = REPO_ROOT) -> str:
    """Hash the dependency declarations, so an unchanged set skips pip.

    :param root: Repository root holding the files.
    :returns: A hex digest over the files' names and bytes.
    """
    digest = hashlib.sha256()
    for name in DEPENDENCY_FILES:
        path = root / name
        digest.update(name.encode("utf-8"))
        digest.update(path.read_bytes() if path.is_file() else b"")
    return digest.hexdigest()


def ensure_venv(total: int) -> Path:
    """Create ``.venv`` and install the dependency set into it, idempotently.

    :param total: Total step count across both stages, for the banners.
    :returns: The venv's Python interpreter.
    """
    step(1, total, "Python 3.12 and the virtualenv")
    check_python()
    python = create_venv(skip=False)
    step(2, total, "Python dependencies")
    fingerprint = dependency_fingerprint()
    if FINGERPRINT.is_file() and FINGERPRINT.read_text(encoding="utf-8").strip() == fingerprint:
        ok("dependency files unchanged since the last install — skipping pip")
        return python
    install_requirements(python, with_prod=False)
    run([str(python), "-m", "pip", "install", "-e", "."])
    FINGERPRINT.write_text(fingerprint + "\n", encoding="utf-8")
    ok("dependencies installed")
    return python
