"""Best-effort infrastructure bring-up (Docker Compose, Alembic).

Both steps are optional conveniences: failures are logged and the launch
continues, because the application degrades gracefully without Postgres,
MinIO or Qdrant (in-memory evidence store, built-in regulatory KB).
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]


def start_docker(mode: str) -> None:
    """Run ``docker compose up -d`` when requested and available.

    :param mode: ``true`` forces the attempt, ``false`` skips it, ``auto``
        starts the stack only when a Docker CLI is on ``PATH``.
    """
    if mode == "false":
        return
    if shutil.which("docker") is None:
        if mode == "true":
            logger.warning("AAA_LAUNCH_DOCKER=true but no docker CLI found.")
        return
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        logger.warning("docker compose up failed: %s", result.stderr.strip()[:400])
    else:
        logger.info("Docker infrastructure is up.")


def run_migrations(mode: str) -> None:
    """Apply Alembic migrations when requested.

    :param mode: ``true`` forces the attempt, ``false`` skips it, ``auto``
        tries once and tolerates an unreachable database.
    """
    if mode == "false":
        return
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        logger.warning("alembic upgrade skipped: %s", result.stderr.strip()[:400])
    else:
        logger.info("Database migrations applied.")
