"""Greedy decoding is pinned on every LLM call, and recorded where it can be checked.

Four real runs of the same case disagreed on 9 of 17 artefact verdicts because
nothing set ``temperature`` or ``seed`` (T-20260913-001). These tests hold the
control in place: the parameters are sent, the Flex ladder's retry and fallback
inherit them, a caller can still override, and what was asked for reaches both
the audit row and the deliverable. This file holds the policy itself; the call path
is ``test_decoding_reaches_the_provider``, the records ``test_decoding_is_recorded``
and ``test_decoding_provenance``.
"""
from __future__ import annotations

import pytest

from aaa.platform.model_registry.decoding import (
    DEFAULT_SEED,
    DEFAULT_TEMPERATURE,
    decoding_kwargs,
    decoding_provenance,
    refuses_temperature,
)

# --------------------------------------------------------------------------- #
# the parameters themselves
# --------------------------------------------------------------------------- #

def test_the_default_is_greedy_with_a_fixed_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reproducibility is the default, not something a caller has to ask for."""
    monkeypatch.delenv("AAA_LLM_TEMPERATURE", raising=False)
    monkeypatch.delenv("AAA_LLM_SEED", raising=False)
    assert decoding_kwargs() == {"temperature": 0.0, "seed": DEFAULT_SEED}
    assert DEFAULT_TEMPERATURE == 0.0


def test_sampling_can_be_opted_into(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exploration stays possible; it just is not what an audit run gets."""
    monkeypatch.setenv("AAA_LLM_TEMPERATURE", "0.7")
    assert decoding_kwargs()["temperature"] == 0.7
    assert decoding_provenance()["greedy_requested"] is False
    assert decoding_provenance()["defaults"] is False


def test_the_seed_can_be_cleared_but_not_accidentally(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty value means 'send none'; an unreadable one falls back to the pin."""
    monkeypatch.setenv("AAA_LLM_SEED", "")
    assert "seed" not in decoding_kwargs()
    monkeypatch.setenv("AAA_LLM_SEED", "not-a-number")
    assert decoding_kwargs()["seed"] == DEFAULT_SEED


def test_an_unreadable_temperature_falls_back_to_greedy(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo in the environment must not silently start sampling."""
    monkeypatch.setenv("AAA_LLM_TEMPERATURE", "warm")
    assert decoding_kwargs()["temperature"] == DEFAULT_TEMPERATURE


def test_an_openai_reasoning_model_is_not_asked_for_a_temperature() -> None:
    """OpenAI rejects any non-default temperature there; asking would fail the call."""
    assert decoding_kwargs("gpt-5.6-terra") == {"seed": DEFAULT_SEED}
    assert decoding_kwargs("openrouter/minimax/minimax-m3") == {
        "temperature": 0.0, "seed": DEFAULT_SEED}


@pytest.mark.parametrize(("model", "refuses"), [
    ("gpt-5.6-terra", True), ("gpt-5.6-sol", True), ("gpt-5", True), ("o3", True),
    ("azure/gpt-5", True), ("gpt-4o-mini", False),
    ("openrouter/minimax/minimax-m3", False),
    ("nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b", False),
    ("no-such-provider/and-no-model", False),
])
def test_only_openai_reasoning_models_refuse_a_temperature(model: str, refuses: bool) -> None:
    """Open-weight reasoning models keep it; that is where it measurably helps."""
    assert refuses_temperature(model) is refuses
