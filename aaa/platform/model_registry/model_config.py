"""model_config.py — the ``ModelConfig`` value type shared by every roster.

Deliberately dependency-free (stdlib only) so both the OpenAI registry
(:mod:`roster`) and the NVIDIA registry (:mod:`nvidia_roster`) can
import it without those two roster modules importing each other.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    """Resolved model + optional service tier for a single agent."""

    model: str
    service_tier: str | None = None
    #: Declared ``max_input_tokens``. Set this for models absent from LiteLLM's
    #: cost map (every ``nvidia_nim/*`` id is), otherwise
    #: :func:`aaa.platform.token_guard.get_context_window` cannot size a budget
    #: and falls back to a generic window — leaving the guard inert for that
    #: model. Populate from the provider's published catalogue only; a guessed
    #: value is worse than a logged unknown.
    context_window: int | None = None

    def litellm_kwargs(self) -> dict[str, Any]:
        """Return kwargs suitable for ``litellm.acompletion(**kwargs, …)``.

        Includes ``service_tier`` only when set, so non-OpenAI providers
        invoked with a fallback model are not handed an unknown param.
        """
        kw: dict[str, Any] = {"model": self.model}
        if self.service_tier is not None:
            kw["service_tier"] = self.service_tier
        return kw
