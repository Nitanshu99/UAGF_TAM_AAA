"""One-shot environment bootstrap for the AAA repository.

Usage::

    python3.12 -m scripts.setup [options]

Steps (each is idempotent; skipped if already done):

1. Verify Python >= 3.12 is invoking this script.
2. Create ``.venv/`` (skipped if it already exists).
3. Upgrade pip + install ``requirements-dev.txt`` (runtime + dev tooling)
   or ``requirements.txt`` with ``--with-prod-deps`` (runtime only).
4. Copy ``.env.example`` → ``.env`` if ``.env`` is missing.
5. (optional) ``docker compose up -d`` to start Postgres/MinIO/Valkey/…
6. (optional) ``alembic upgrade head`` to apply DB migrations.
7. Run the test suite (``pytest -m "not e2e"``) as a smoke test.
8. Print next-step commands.

Flags: ``--no-venv``, ``--no-docker``, ``--no-migrate``, ``--no-tests``,
``--with-prod-deps``; see ``--help``.

Exit codes: 0 — all requested steps completed; 1 — a required step failed.
"""
from __future__ import annotations

from scripts.setup.main import main

__all__ = ["main"]
