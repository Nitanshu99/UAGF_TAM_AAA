"""Where the OpenRouter key comes from: the flag, the environment, ``.env``, or the terminal."""
from __future__ import annotations

import getpass
import os
import sys

from scripts.bootstrap.steps.dotenv.defaults import is_placeholder
from scripts.setup.console import err


def prompt_for_key() -> str:
    """Ask for the OpenRouter key on a terminal; exit when there is none.

    :returns: The key as typed (input hidden).
    """
    if not sys.stdin.isatty():
        err("no OpenRouter key: pass --openrouter-key, set OPENROUTER_API_KEY, "
            "or put it in .env (https://openrouter.ai/keys)")
        sys.exit(1)
    key = getpass.getpass("OpenRouter API key (sk-or-v1-…, input hidden): ").strip()
    if not key:
        err("an OpenRouter key is required")
        sys.exit(1)
    return key


def resolve_key(explicit: str | None, current: dict[str, str], mock: bool) -> str:
    """The key to write, from the first source that has one.

    :param explicit: ``--openrouter-key``, if given.
    :param current: What ``.env`` says now.
    :param mock: Whether a missing key is acceptable (the stub needs none).
    :returns: The key, or ``""`` for a mock run without one.
    """
    resolved = explicit or os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not resolved and not is_placeholder(current.get("OPENROUTER_API_KEY")):
        resolved = current["OPENROUTER_API_KEY"]
    if not resolved and not mock:
        resolved = prompt_for_key()
    return resolved


__all__ = ["prompt_for_key", "resolve_key"]
