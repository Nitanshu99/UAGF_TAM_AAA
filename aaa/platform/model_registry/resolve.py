"""Resolve an agent name to its :class:`ModelConfig` under the active provider."""
from __future__ import annotations

from aaa.platform.model_registry.model_config import ModelConfig
from aaa.platform.model_registry.roster import AGENT_MODELS


def _active_roster() -> dict[str, ModelConfig]:
    """Return the roster for the active provider.

    ``AGENT_MODELS`` by default, the NVIDIA NIM mirror under
    ``PROVIDER=nvidia``, or the OpenRouter mirror under
    ``PROVIDER=openrouter``.

    Imports are deferred (called at request time, not module load) so the
    provider gate — and the NVIDIA key check behind it — runs when a model is
    asked for, not when the registry is imported.
    """
    from aaa.platform.model_registry.provider import (  # pylint: disable=import-outside-toplevel
        NVIDIA,
        OPENROUTER,
        active_provider,
        ensure_nvidia_key,
    )
    provider = active_provider()
    if provider == OPENROUTER:
        from aaa.platform.model_registry.openrouter.roster import (  # pylint: disable=import-outside-toplevel
            OPENROUTER_AGENT_MODELS,
        )
        return OPENROUTER_AGENT_MODELS
    if provider != NVIDIA:
        return AGENT_MODELS
    ensure_nvidia_key()
    from aaa.platform.model_registry.nvidia_roster import (  # pylint: disable=import-outside-toplevel
        NVIDIA_AGENT_MODELS,
    )
    return NVIDIA_AGENT_MODELS


def get_model_config(agent_name: str) -> ModelConfig:
    """Return :class:`ModelConfig` for *agent_name* under the active provider.

    Raises :class:`KeyError` if the agent is not registered — surfacing typos
    at construction time rather than at the first LLM call.
    """
    return _active_roster()[agent_name]


def resolve_model(agent_name: str, override: str | None = None) -> str:
    """Return *override* if non-empty, else the active-provider default."""
    if override:
        return override
    return _active_roster()[agent_name].model


__all__ = ["get_model_config", "resolve_model"]
