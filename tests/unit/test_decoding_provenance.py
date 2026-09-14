"""The deliverable says whether greedy decoding actually applied, per roster model.

A reader comparing two runs needs to know which kind of disagreement to expect.
The request alone cannot say: the default OpenAI roster asks for greedy decoding
and cannot have it. So the stamp resolves it for every model on the active roster
(T-20260913-003), using LiteLLM's real mapping.
"""
from __future__ import annotations

import pytest

from aaa.platform.model_registry.decoding import DEFAULT_SEED
from aaa.platform.state.run_integrity import build_run_integrity

GREEDY = {"temperature": 0.0, "seed": DEFAULT_SEED}


def test_the_deliverable_says_greedy_did_not_apply_on_openai(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The default roster asks for greedy and cannot get it; the stamp must not hide that."""
    monkeypatch.delenv("PROVIDER", raising=False)
    stamp = build_run_integrity({"phase_artefacts": {}})["decoding"]
    assert stamp["greedy_requested"] is True
    assert stamp["greedy_applied"] is False
    assert stamp["sent_by_model"]["gpt-5.6-terra"] == {"seed": DEFAULT_SEED}


def test_the_deliverable_says_greedy_applied_on_openrouter(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The route the RCA runs used does receive it, and the stamp says so."""
    monkeypatch.setenv("PROVIDER", "openrouter")
    stamp = build_run_integrity({"phase_artefacts": {}})["decoding"]
    assert stamp["greedy_applied"] is True
    assert all(wire == GREEDY for wire in stamp["sent_by_model"].values())
