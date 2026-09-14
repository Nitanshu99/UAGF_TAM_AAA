"""Fix 48 — a phase's artefacts are critiqued concurrently (finding R16).

The Verifier is the most expensive agent in the system, in every case of the
2026-09-03 run: 43 %-61 % of each engagement's LLM wall-clock. Its calls were
serial, and they did not need to be — each artefact is critiqued independently.

The acceptance criteria are about what must *not* change: per-artefact verdicts
stay per-artefact, no critique is skipped, and fix 20's `unverified` path still
fires for a genuine failure.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from aaa.agents.tier1.phases.verification import verify_artefacts as mod
from aaa.agents.tier1.verifier.verdicts import UNVERIFIED

P3 = {"T09_model_card": ["Art.13"], "T10_explainability_report": ["Art.13"],
      "T11_robustness_report": ["Art.15"]}


class _Verifier:
    """Records overlap: how many critiques were in flight at once."""

    def __init__(self, verdicts: dict[str, str] | None = None,
                 delay: float = 0.05, raises: set[str] | None = None):
        self.verdicts = verdicts or {}
        self.delay = delay
        self.raises = raises or set()
        self.inflight = 0
        self.peak = 0
        self.seen: list[str] = []

    async def process(self, message: dict) -> dict:
        tid = message["template_id"]
        self.seen.append(tid)
        self.inflight += 1
        self.peak = max(self.peak, self.inflight)
        try:
            await asyncio.sleep(self.delay)
            if tid in self.raises:
                raise RuntimeError("provider down")
            return {"verdict": self.verdicts.get(tid, "accept"), "issues": [],
                    "scores": {"factual_accuracy": 1}}
        finally:
            self.inflight -= 1


class _Agent:
    name = "ModelValidator"
    store = None


def _run(verifier: _Verifier, tids: dict[str, list[str]] | None = None,
         state: dict | None = None) -> str:
    state = state if state is not None else {"verifier_critiques": {},
                                             "phase_artefacts": {}}
    return asyncio.run(mod._verify_artefacts(
        verifier, _Agent(), {"phase_id": "P3"}, state, tids or P3,
        "Phase 3 ModelValidator", 0.9, 0))


# --------------------------------------------------------------------------- #
# concurrent, and measurably so
# --------------------------------------------------------------------------- #

def test_a_phases_artefacts_are_critiqued_at_the_same_time():
    verifier = _Verifier()
    _run(verifier)
    assert verifier.peak == 3, "three independent critiques, three in flight"


def test_the_wall_clock_is_the_slowest_call_not_their_sum():
    verifier = _Verifier(delay=0.1)
    started = time.monotonic()
    _run(verifier)
    elapsed = time.monotonic() - started
    assert elapsed < 0.3, f"{elapsed:.2f}s — serial would be ~0.3s"


def test_the_burst_is_bounded(monkeypatch):
    monkeypatch.setattr(mod, "MAX_CONCURRENT_CRITIQUES", 2)
    verifier = _Verifier()
    _run(verifier)
    assert verifier.peak == 2


def test_a_cap_of_one_is_exactly_the_old_serial_behaviour(monkeypatch):
    monkeypatch.setattr(mod, "MAX_CONCURRENT_CRITIQUES", 1)
    verifier = _Verifier()
    _run(verifier)
    assert verifier.peak == 1
    assert verifier.seen == list(P3)


# --------------------------------------------------------------------------- #
# nothing an audit needs is traded for the time
# --------------------------------------------------------------------------- #

def test_every_artefact_is_still_critiqued():
    verifier = _Verifier()
    state = {"verifier_critiques": {}, "phase_artefacts": {}}
    _run(verifier, state=state)
    assert set(verifier.seen) == set(P3)
    assert set(state["verifier_critiques"]) == set(P3)


def test_each_verdict_stays_attributable_to_its_own_artefact():
    verifier = _Verifier({"T09_model_card": "rerun",
                          "T10_explainability_report": "accept",
                          "T11_robustness_report": "escalate_hitl"})
    state = {"verifier_critiques": {}, "phase_artefacts": {}}
    _run(verifier, state=state)
    got = {tid: c["verdict"] for tid, c in state["verifier_critiques"].items()}
    assert got == {"T09_model_card": "rerun",
                   "T10_explainability_report": "accept",
                   "T11_robustness_report": "escalate_hitl"}


def test_the_worst_verdict_does_not_depend_on_completion_order():
    """The fold runs afterwards, in contract order, not in whoever-finished order."""
    verdicts = {"T09_model_card": "accept", "T10_explainability_report": "escalate_hitl",
                "T11_robustness_report": "accept_with_notes"}
    first = _run(_Verifier(verdicts, delay=0.01))
    second = _run(_Verifier(verdicts, delay=0.0))
    assert first == second == "escalate_hitl"


def test_fix_20s_unverified_path_still_fires_for_a_genuine_failure():
    verifier = _Verifier(raises={"T10_explainability_report"})
    state = {"verifier_critiques": {}, "phase_artefacts": {}}
    worst = _run(verifier, state=state)
    crit = state["verifier_critiques"]["T10_explainability_report"]
    assert crit["verdict"] == UNVERIFIED
    assert crit["llm_fallback_mode"] is True
    assert worst == UNVERIFIED or worst == "unverified"


def test_one_failure_does_not_cancel_its_siblings():
    verifier = _Verifier(raises={"T09_model_card"})
    state = {"verifier_critiques": {}, "phase_artefacts": {}}
    _run(verifier, state=state)
    assert set(state["verifier_critiques"]) == set(P3)
    assert state["verifier_critiques"]["T11_robustness_report"]["verdict"] == "accept"


def test_a_single_artefact_phase_is_unaffected():
    verifier = _Verifier()
    assert _run(verifier, {"T16_uagf_tam_l_evidence": ["Art.15"]}) == "accept"
    assert verifier.peak == 1


# --------------------------------------------------------------------------- #
# the cap is configurable, because a provider quota is not ours to assume
# --------------------------------------------------------------------------- #

def test_the_default_covers_the_widest_phase():
    assert mod._max_concurrent() == 3


def test_an_operator_may_lower_it(monkeypatch):
    monkeypatch.setenv("MAX_CONCURRENT_CRITIQUES", "1")
    assert mod._max_concurrent() == 1


def test_a_nonsense_value_falls_back_rather_than_crashing(monkeypatch):
    monkeypatch.setenv("MAX_CONCURRENT_CRITIQUES", "lots")
    assert mod._max_concurrent() == 3


@pytest.mark.parametrize("raw,expected", [("0", 1), ("-4", 1), ("8", 8)])
def test_the_cap_is_never_below_one(monkeypatch, raw, expected):
    monkeypatch.setenv("MAX_CONCURRENT_CRITIQUES", raw)
    assert mod._max_concurrent() == expected
