"""Bootstrap steps grouped by concern (environment setup, infra bring-up)."""
from __future__ import annotations

from scripts.setup.steps.env import check_python, copy_env, create_venv, install_requirements
from scripts.setup.steps.infra import alembic_migrate, docker_up, smoke_test

__all__ = [
    "alembic_migrate",
    "check_python",
    "copy_env",
    "create_venv",
    "docker_up",
    "install_requirements",
    "smoke_test",
]
