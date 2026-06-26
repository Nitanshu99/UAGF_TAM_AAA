#!/usr/bin/env python3
"""
scripts/setup.py — One-shot environment bootstrap for the AAA repository.

Usage::

    python3.12 scripts/setup.py [options]

Steps (each is idempotent; skipped if already done):
  1. Verify Python >= 3.12 is invoking this script.
  2. Create ``.venv/`` (skipped if it already exists).
  3. Upgrade pip + install ``requirements-dev.txt`` (runtime + dev tooling) or
     ``requirements.txt`` with ``--with-prod-deps`` (runtime only) inside the
     venv.
  4. Copy ``.env.example`` -> ``.env`` if ``.env`` is missing.
  5. (optional) ``docker compose up -d`` to start Postgres/MinIO/Valkey/...
  6. (optional) ``alembic upgrade head`` to apply DB migrations.
  7. Run the offline test suite (``pytest -m "not e2e"``) as a smoke test.
  8. Print next-step commands.

Flags:
  --no-venv          Reuse the current interpreter, do not create ``.venv/``.
  --no-docker        Skip ``docker compose up -d``.
  --no-migrate       Skip ``alembic upgrade head``.
  --no-tests         Skip the smoke-test pytest run.
  --with-prod-deps   Install ``requirements.txt`` (runtime only) instead of
                     ``requirements-dev.txt`` (runtime + dev tooling).
  -h, --help         Show this help and exit.

Exit codes:
  0 - all requested steps completed successfully.
  1 - a required step failed (details printed to stderr).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = REPO_ROOT / ".venv"
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
REQ_DEV = REPO_ROOT / "requirements-dev.txt"
REQ_PROD = REPO_ROOT / "requirements.txt"

MIN_PY = (3, 12)


# ── Pretty printing ─────────────────────────────────────────────────────────

def _step(n: int, total: int, msg: str) -> None:
    print(f"\n\033[1;36m[{n}/{total}] {msg}\033[0m", flush=True)


def _ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m {msg}", flush=True)


def _warn(msg: str) -> None:
    print(f"  \033[33m!\033[0m {msg}", flush=True)


def _err(msg: str) -> None:
    print(f"  \033[31m✗\033[0m {msg}", file=sys.stderr, flush=True)


# ── Subprocess helpers ──────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path | None = None, check: bool = True,
         env: dict[str, str] | None = None) -> int:
    print(f"  $ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd or REPO_ROOT), env=env)
    if check and proc.returncode != 0:
        _err(f"command failed (exit {proc.returncode}): {' '.join(cmd)}")
        sys.exit(1)
    return proc.returncode


def _load_dotenv(path: Path) -> dict[str, str]:
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


def _venv_bin(name: str) -> Path:
    """Return the path to ``name`` inside ``.venv/`` (Windows-aware)."""
    sub = "Scripts" if os.name == "nt" else "bin"
    return VENV_DIR / sub / name


# ── Steps ───────────────────────────────────────────────────────────────────

def check_python() -> None:
    if sys.version_info < MIN_PY:
        _err(
            f"Python {MIN_PY[0]}.{MIN_PY[1]}+ required; "
            f"this interpreter is {sys.version.split()[0]}. "
            f"Re-run with: python3.12 scripts/setup.py"
        )
        sys.exit(1)
    _ok(f"Python {sys.version.split()[0]} (>= {MIN_PY[0]}.{MIN_PY[1]})")


def create_venv(skip: bool) -> Path:
    if skip:
        _warn("--no-venv: reusing current interpreter")
        return Path(sys.executable)
    if VENV_DIR.exists():
        _ok(f"virtualenv already present at {VENV_DIR.relative_to(REPO_ROOT)}/")
    else:
        _run([sys.executable, "-m", "venv", str(VENV_DIR)])
        _ok(f"created {VENV_DIR.relative_to(REPO_ROOT)}/")
    return _venv_bin("python")


def install_requirements(py: Path, with_prod: bool) -> None:
    req = REQ_PROD if with_prod else REQ_DEV
    if not req.exists():
        _err(f"requirements file missing: {req}")
        sys.exit(1)
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(py), "-m", "pip", "install", "-r", str(req)])
    _ok(f"installed {req.name}")


def copy_env() -> None:
    if ENV_FILE.exists():
        _ok(".env already present")
        return
    if not ENV_EXAMPLE.exists():
        _warn(".env.example missing — skipping")
        return
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    _ok("created .env from .env.example (edit it before running with real secrets)")


def docker_up(skip: bool) -> None:
    if skip:
        _warn("--no-docker: skipping docker compose up -d")
        return
    if shutil.which("docker") is None:
        _warn("docker not found on PATH — skipping (install Docker Desktop to enable)")
        return
    _run(["docker", "compose", "up", "-d"])
    _ok("docker compose stack running")


def alembic_migrate(py: Path, skip: bool) -> None:
    if skip:
        _warn("--no-migrate: skipping alembic upgrade head")
        return
    if not (REPO_ROOT / "alembic.ini").exists():
        _warn("alembic.ini missing — skipping")
        return
    env = os.environ.copy()
    env.update(_load_dotenv(ENV_FILE))
    rc = _run([str(py), "-m", "alembic", "upgrade", "head"], check=False, env=env)
    if rc != 0:
        _warn("alembic failed (DB not reachable?); continuing — re-run later with: "
              "python -m alembic upgrade head")
    else:
        _ok("alembic migrations applied")


def smoke_test(py: Path, skip: bool) -> None:
    if skip:
        _warn("--no-tests: skipping smoke test")
        return
    env = os.environ.copy()
    env["AAA_OFFLINE_MODE"] = "true"
    cmd = [str(py), "-m", "pytest", "-q", "-m", "not e2e", "--no-cov"]
    print(f"  $ AAA_OFFLINE_MODE=true {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env)
    if proc.returncode != 0:
        _err(f"smoke test failed (exit {proc.returncode})")
        sys.exit(1)
    _ok("smoke test passed")


def print_next_steps(py: Path) -> None:
    activate = ". .venv/bin/activate" if os.name != "nt" else ".venv\\Scripts\\activate"
    print(
        "\n\033[1;32m✓ Setup complete.\033[0m\n\n"
        "Next steps:\n"
        f"  1. Activate the venv:   {activate}\n"
        "  2. Edit .env with real LLM API keys (optional in offline mode).\n"
        "  3. Run the offline demo: make intake-demo\n"
        "  4. Start FastAPI:        uvicorn aaa.api.main:app --reload\n"
        "  5. Start Streamlit:      AAA_OFFLINE_MODE=true streamlit run aaa/ui/app.py\n"
        "  6. Read USER_MANUAL.md for the full developer guide.\n"
    )


# ── Entry point ─────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="scripts/setup.py",
        description="One-shot environment bootstrap for the AAA repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--no-venv", action="store_true",
                   help="Reuse the current interpreter; do not create .venv/.")
    p.add_argument("--no-docker", action="store_true",
                   help="Skip 'docker compose up -d'.")
    p.add_argument("--no-migrate", action="store_true",
                   help="Skip 'alembic upgrade head'.")
    p.add_argument("--no-tests", action="store_true",
                   help="Skip the offline pytest smoke run.")
    p.add_argument("--with-prod-deps", action="store_true",
                   help="Install requirements.txt (runtime only) instead of "
                        "requirements-dev.txt (runtime + dev tooling).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    total = 7

    _step(1, total, "Verify Python version")
    check_python()

    _step(2, total, "Create virtualenv")
    py = create_venv(skip=args.no_venv)

    _step(3, total, "Install Python dependencies")
    install_requirements(py, with_prod=args.with_prod_deps)

    _step(4, total, "Copy .env.example -> .env")
    copy_env()

    _step(5, total, "Start docker compose stack")
    docker_up(skip=args.no_docker)

    _step(6, total, "Apply alembic migrations")
    alembic_migrate(py, skip=args.no_migrate)

    _step(7, total, "Run offline smoke test")
    smoke_test(py, skip=args.no_tests)

    print_next_steps(py)
    return 0


if __name__ == "__main__":
    sys.exit(main())
