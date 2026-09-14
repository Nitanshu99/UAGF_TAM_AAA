"""What every LLM call asks the provider for: greedy, with a fixed seed.

Override for deliberate exploration: ``AAA_LLM_TEMPERATURE`` and ``AAA_LLM_SEED``
(set the seed empty to send none at all). An unreadable value falls back to the
pin, so a typo in the environment cannot silently start sampling.
"""
from __future__ import annotations

import os
from typing import Any

from aaa.platform.model_registry.decoding.capability import refuses_temperature

#: Greedy. Reproducibility outranks diversity for an assurance engagement.
DEFAULT_TEMPERATURE = 0.0

#: Any fixed value does; it is pinned so two runs ask the provider for the same
#: sample rather than leaving it to chance.
DEFAULT_SEED = 42


def _temperature() -> float:
    """The configured temperature, falling back to greedy on anything unreadable."""
    raw = os.environ.get("AAA_LLM_TEMPERATURE", "").strip()
    try:
        return float(raw) if raw else DEFAULT_TEMPERATURE
    except ValueError:
        return DEFAULT_TEMPERATURE


def _seed() -> int | None:
    """The configured seed, or ``None`` when the caller asked for none."""
    if "AAA_LLM_SEED" not in os.environ:
        return DEFAULT_SEED
    raw = os.environ["AAA_LLM_SEED"].strip()
    try:
        return int(raw) if raw else None
    except ValueError:
        return DEFAULT_SEED


def decoding_kwargs(model: str = "") -> dict[str, Any]:
    """The decoding parameters an LLM call to *model* is made with.

    :param model: LiteLLM model string. Without one, the policy as configured.
    :returns: ``temperature`` unless *model* refuses one (see
        :mod:`~aaa.platform.model_registry.decoding.capability`), and ``seed``
        unless it was explicitly cleared.
    """
    kwargs: dict[str, Any] = ({} if refuses_temperature(model)
                              else {"temperature": _temperature()})
    seed = _seed()
    if seed is not None:
        kwargs["seed"] = seed
    return kwargs


__all__ = ["DEFAULT_SEED", "DEFAULT_TEMPERATURE", "decoding_kwargs"]
