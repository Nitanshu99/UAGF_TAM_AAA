"""Launch configuration resolved from environment variables.

Every knob has a sensible default so ``python -m aaa`` works on a fresh
clone with nothing but Python installed.

:envvar AAA_LAUNCH_DOCKER:   ``auto`` (default), ``true`` or ``false`` —
    start the Docker Compose infrastructure before the app.
:envvar AAA_LAUNCH_MIGRATE:  run Alembic migrations on start (default ``auto``).
:envvar AAA_LAUNCH_API:      start the FastAPI backend (default ``true``).
:envvar AAA_LAUNCH_UI:       start the Streamlit UI (default ``true``).
:envvar PLATFORM_PORT:       FastAPI port (default ``8000``).
:envvar STREAMLIT_SERVER_PORT: Streamlit port (default ``8501``).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

_TRUE = {"1", "true", "yes", "on"}


def _flag(name: str, default: str) -> str:
    """Return the lower-cased value of environment variable *name*.

    :param name: Environment variable to read.
    :param default: Value used when the variable is unset or blank.
    :returns: The resolved, lower-cased setting.
    """
    return (os.environ.get(name) or default).strip().lower()


@dataclass(frozen=True)
class LaunchConfig:
    """Resolved launch plan for :mod:`aaa.launcher`."""

    docker: str
    migrate: str
    api: bool
    ui: bool
    api_port: int
    ui_port: int


def load_config() -> LaunchConfig:
    """Build a :class:`LaunchConfig` from the current environment.

    :returns: Immutable launch configuration.
    """
    return LaunchConfig(
        docker=_flag("AAA_LAUNCH_DOCKER", "auto"),
        migrate=_flag("AAA_LAUNCH_MIGRATE", "auto"),
        api=_flag("AAA_LAUNCH_API", "true") in _TRUE,
        ui=_flag("AAA_LAUNCH_UI", "true") in _TRUE,
        api_port=int(os.environ.get("PLATFORM_PORT", "8000")),
        ui_port=int(os.environ.get("STREAMLIT_SERVER_PORT", "8501")),
    )
