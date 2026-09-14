"""The environment the ingester, the API, the UI and the browser all see."""
from __future__ import annotations

import os
import re
from pathlib import Path

from scripts.bootstrap.envfile import raw_values

#: A ``${VAR}`` or ``${VAR:-default}`` reference inside a ``.env`` value.
_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def child_env(env_file: Path, overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Compose the process environment for everything the bootstrap starts.

    Same precedence as the application's own loader: the shell wins over
    ``.env``. The bootstrap's own overrides (the ``--mock-llm`` gateway) win
    over both, because they are the point of the option.

    :param env_file: The ``.env`` file.
    :param overrides: Values that must apply regardless.
    :returns: A complete environment mapping.
    """
    env = raw_values(env_file)
    env.update(os.environ)
    env.update(overrides or {})
    # ``${VAR}`` is resolved after the shell is merged in, so an exported POSTGRES_PORT
    # reaches DATABASE_URL as it reaches docker compose (T-20260914-068).
    env = {key: _REFERENCE.sub(lambda m: env.get(m.group(1), m.group(2) or ""), value)
           for key, value in env.items()}
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def port(env: dict[str, str], key: str, default: int) -> int:
    """Read a port from *env*, tolerating blanks.

    :param env: Environment mapping.
    :param key: Variable name.
    :param default: Value when unset or blank.
    :returns: The port number.
    """
    raw = (env.get(key) or "").strip()
    return int(raw) if raw.isdigit() else default
