"""The run-level stamp: what was asked for, and whether each model received it.

A reader comparing two runs needs to know which kind of disagreement to expect.
Under greedy decoding a changed verdict is a finding; under sampling it may be
nothing but the sample. The request alone cannot answer that, because a reasoning
model on OpenAI drops the temperature — so the stamp resolves it per model.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.model_registry.decoding.policy import (
    DEFAULT_SEED,
    DEFAULT_TEMPERATURE,
    decoding_kwargs,
)
from aaa.platform.model_registry.decoding.wire import sent_decoding


def _roster_models() -> list[str]:
    """Every distinct model string on the active provider's roster."""
    from aaa.platform.model_registry.resolve import _active_roster

    try:
        return sorted({config.model for config in _active_roster().values()})
    except Exception:  # noqa: BLE001 - e.g. PROVIDER=nvidia with no key, outside a run
        return []


def decoding_provenance() -> dict[str, Any]:
    """What was asked for, what each roster model was sent, and whether greedy held.

    :returns: The request, ``greedy_requested``, ``defaults``, ``sent_by_model``
        and ``greedy_applied`` — true only when every roster model was sent
        ``temperature=0``.
    """
    requested = decoding_kwargs()
    sent = {model: sent_decoding(model) for model in _roster_models()}
    applied = bool(sent) and all(
        wire is not None and wire.get("temperature") == 0.0 for wire in sent.values())
    return {**requested,
            "greedy_requested": requested["temperature"] == 0.0,
            "defaults": (requested["temperature"] == DEFAULT_TEMPERATURE
                         and requested.get("seed") == DEFAULT_SEED),
            "sent_by_model": sent,
            "greedy_applied": applied}


__all__ = ["decoding_provenance"]
