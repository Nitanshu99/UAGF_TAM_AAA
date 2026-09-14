"""Step 3: the tools and files the rest of the bootstrap cannot do without."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from scripts.bootstrap.steps.bundles import BUNDLES
from scripts.setup.console import err, ok


def _capture(cmd: list[str]) -> tuple[int, str]:
    """Run *cmd* quietly; return its exit code and combined output."""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def check_docker() -> None:
    """Exit unless the Docker CLI, Compose v2 and a running daemon are present."""
    if shutil.which("docker") is None:
        err("docker is not on PATH — install Docker Desktop (https://docs.docker.com/get-docker/)")
        sys.exit(1)
    code, version = _capture(["docker", "compose", "version", "--short"])
    if code != 0 or not version[:1].isdigit() or int(version.split(".")[0]) < 2:
        err(f"docker compose v2 is required (got {version or 'nothing'})")
        sys.exit(1)
    code, out = _capture(["docker", "info", "--format", "{{.ServerVersion}}"])
    if code != 0:
        err("the Docker daemon is not running — start Docker Desktop and re-run")
        sys.exit(1)
    ok(f"docker {out} · compose {version}")


def check_bundles(zip_dir: Path) -> dict[str, Path]:
    """Locate the two bundles; exit naming whichever is missing.

    :param zip_dir: Directory expected to hold them.
    :returns: Bundle file name → path.
    """
    found = {b.name: zip_dir / b.name for b in BUNDLES}
    missing = [name for name, path in found.items() if not path.is_file()]
    if missing:
        for name in missing:
            err(f"{zip_dir / name} is missing")
        err("mariposa.zip (the Mariposa intake bundle) and corpus.zip (the regulatory "
            "corpus) are provided separately, not with the repository: put both in "
            f"{zip_dir} and re-run.")
        sys.exit(1)
    for name, path in found.items():
        ok(f"{name} ({path.stat().st_size // 1024} KB)")
    return found
