"""Step 4: a ``.env`` that runs the whole stack on one OpenRouter key."""
from __future__ import annotations

import shutil
from pathlib import Path

from scripts.bootstrap.envfile import read_values, set_values
from scripts.bootstrap.steps.dotenv.defaults import FIXED, REFERENCE, VENDOR_KEYS, is_placeholder
from scripts.bootstrap.steps.dotenv.key import resolve_key
from scripts.bootstrap.steps.dotenv.provision import langfuse_provisioning
from scripts.setup.console import ok, warn


def _langfuse_updates(fresh: bool, current: dict[str, str]) -> dict[str, str]:
    """Provision Langfuse on a fresh ``.env``; warn when an old one has it blank."""
    if fresh:
        ok("Langfuse provisioned: project keys, admin login and server secrets generated")
        return langfuse_provisioning()
    if is_placeholder(current.get("LANGFUSE_PUBLIC_KEY")):
        warn("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are blank in the existing .env — "
             "LLM tracing stays off (see SETUP.md §8)")
    return {}


def configure_env(env_file: Path, example: Path, key: str | None, mock: bool) -> dict[str, str]:
    """Create or update ``.env`` and return what it now says.

    :param env_file: The ``.env`` to write.
    :param example: ``.env.example``, copied when ``.env`` is absent.
    :param key: Explicit OpenRouter key, if given.
    :param mock: Whether a missing key is acceptable (the stub needs none).
    :returns: The resulting values.
    """
    fresh = not env_file.is_file()
    if fresh:
        shutil.copy(example, env_file)
        ok("created .env from .env.example")
    current = read_values(env_file)
    updates = dict(FIXED)
    updates.update({k: "" for k in VENDOR_KEYS if is_placeholder(current.get(k))})
    updates.update({k: v for k, v in REFERENCE.items() if is_placeholder(current.get(k))})
    updates.update(_langfuse_updates(fresh, current))
    resolved = resolve_key(key, current, mock)
    updates["OPENROUTER_API_KEY"] = resolved
    set_values(env_file, updates)
    ok("PROVIDER=openrouter for the agent roster and all three embedding purposes"
       + ("" if resolved else " (no key: --mock-llm stub only)"))
    return read_values(env_file)


__all__ = ["configure_env"]
