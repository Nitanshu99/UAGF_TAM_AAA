"""Bootstrap steps 5–7: Docker stack, migrations, smoke test."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.setup.console import err, ok, warn
from scripts.setup.paths import ENV_FILE, REPO_ROOT
from scripts.setup.shell import load_dotenv, run


def docker_up(skip: bool) -> None:
    """Start the docker compose stack (best effort)."""
    if skip:
        warn("--no-docker: skipping docker compose up -d")
        return
    if shutil.which("docker") is None:
        warn("docker not found on PATH — skipping (install Docker Desktop to enable)")
        return
    run(["docker", "compose", "up", "-d"])
    ok("docker compose stack running")


def alembic_migrate(py: Path, skip: bool) -> None:
    """Apply alembic migrations, tolerating an unreachable database."""
    if skip:
        warn("--no-migrate: skipping alembic upgrade head")
        return
    if not (REPO_ROOT / "alembic.ini").exists():
        warn("alembic.ini missing — skipping")
        return
    env = os.environ.copy()
    env.update(load_dotenv(ENV_FILE))
    rc = run([str(py), "-m", "alembic", "upgrade", "head"], check=False, env=env)
    if rc != 0:
        warn("alembic failed (DB not reachable?); continuing — re-run later with: "
             "python -m alembic upgrade head")
    else:
        ok("alembic migrations applied")


def smoke_test(py: Path, skip: bool) -> None:
    """Run the non-e2e pytest suite as a smoke test."""
    if skip:
        warn("--no-tests: skipping smoke test")
        return
    cmd = [str(py), "-m", "pytest", "-q", "-m", "not e2e", "--no-cov"]
    print(f"  $ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=os.environ.copy(), check=False)
    if proc.returncode != 0:
        err(f"smoke test failed (exit {proc.returncode})")
        sys.exit(1)
    ok("smoke test passed")
