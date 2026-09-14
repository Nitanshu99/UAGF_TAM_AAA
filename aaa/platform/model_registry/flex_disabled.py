"""The Flex service-tier switch: whether an agent may use OpenAI Flex right now."""
from __future__ import annotations

import os

from aaa.platform.model_registry.roster import AGENT_MODELS


def _flex_disabled() -> bool:
    """True when ``AAA_DISABLE_FLEX`` is set — backends without OpenAI Flex support.

    Read at call time (agent construction) so it can be toggled per process via env.
    """
    return os.environ.get("AAA_DISABLE_FLEX", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def resolve_service_tier(
    agent_name: str, override: str | None = None
) -> str | None:
    """Return *override* if provided, else the registry service tier.

    Global kill-switch: when ``AAA_DISABLE_FLEX`` is truthy, no ``service_tier`` is
    sent at all, so providers that reject the ``flex`` processing tier do not error
    (which would otherwise force those agents onto the deterministic fallback).
    """
    if _flex_disabled():
        return None
    if override is not None:
        return override
    return AGENT_MODELS[agent_name].service_tier


__all__ = [
    "resolve_service_tier",
]
