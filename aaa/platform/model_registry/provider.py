"""provider.py — active LLM provider switch (``nvidia`` default | ``openai`` | ``openrouter``).

Reads the ``PROVIDER`` env var so the whole agent roster can be redirected
without touching any agent code. When NVIDIA is selected, propagates this
repo's ``NVIDIA_API_KEY`` into ``NVIDIA_NIM_API_KEY`` — the env var LiteLLM's
``nvidia_nim/`` provider prefix actually reads — so one key in ``.env`` covers
both names. OpenRouter needs no such aliasing: LiteLLM's ``openrouter/``
prefix reads ``OPENROUTER_API_KEY`` directly.
"""
from __future__ import annotations

import os

NVIDIA: str = "nvidia"
OPENAI: str = "openai"
OPENROUTER: str = "openrouter"

#: Providers with a roster mirror; anything else falls back to OpenAI.
_KNOWN: frozenset[str] = frozenset({NVIDIA, OPENAI, OPENROUTER})


def active_provider() -> str:
    """Return the active provider.

    :returns: Normalized value of the ``PROVIDER`` env var; unset, blank, or
        unrecognised falls back to ``"openai"``.
    :rtype: str
    """
    raw = os.environ.get("PROVIDER", "").strip().lower()
    return raw if raw in _KNOWN else OPENAI


def ensure_nvidia_key() -> None:
    """Propagate ``NVIDIA_API_KEY`` into ``NVIDIA_NIM_API_KEY`` for LiteLLM.

    No-op when ``NVIDIA_NIM_API_KEY`` is already set or no source key exists.

    :returns: None
    """
    if os.environ.get("NVIDIA_NIM_API_KEY"):
        return
    source = os.environ.get("NVIDIA_API_KEY")
    if source:
        os.environ["NVIDIA_NIM_API_KEY"] = source
