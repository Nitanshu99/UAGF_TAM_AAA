"""Fix 32 (Q8) — one mechanism re-runs a phase, and it is the phase's own loop.

Phase 3 was dispatched twice in the part-2 run, for 1,344 s combined. Its own
rerun loop declined — T09 escalated, `escalate_hitl` outranks `rerun` in
`_VERDICT_ORDER`, and the loop only reran when `rerun` was the phase's *worst*
verdict — so T11's `rerun` was silently dropped. The Orchestrator then noticed
exactly that (*"T11 received a 'rerun' verdict with 0 reruns used"*) and
re-dispatched the whole phase itself: 907 s on top of 436, with no
`rerun_context` and a second set of gate entries.

The division is now stated: **an artefact that exists and was rejected is the
phase loop's; a phase that has delivered nothing is the Orchestrator's.**
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aaa.agents.tier1.orchestrator.react import Decision
from aaa.agents.tier1.orchestrator.react.guards import _PHASE_CAP, apply_guards
from aaa.agents.tier1.phases.verification.rerun_context import rerun_requested
from aaa.agents.tier1.verifier import MAX_RERUNS

T09, T11 = "T09_model_card", "T11_robustness_report"
P3 = {T09: ["Art.13", "Art.15"], T11: ["Art.15"]}


def _critiques(**verdicts: str) -> dict:
    return {"verifier_critiques": {tid: {"verdict": verdict}
                                   for tid, verdict in verdicts.items()}}


# ── the phase loop honours a rerun a sibling's escalation used to mask ───────

def test_the_run_s_own_case_a_rerun_beside_an_escalation():
    """T09 escalated, T11 was sent back; only T11 needs another attempt."""
    state = _critiques(**{T09: "escalate_hitl", T11: "rerun"})

    assert rerun_requested(state, list(P3)) == [T11]


@pytest.mark.parametrize("verdicts,expected", [
    ({T09: "accept", T11: "accept"}, []),
    ({T09: "escalate_hitl", T11: "accept"}, []),
    ({T09: "unverified", T11: "accept_with_notes"}, []),
    ({T09: "rerun", T11: "rerun"}, [T09, T11]),
])
def test_only_a_rerun_verdict_asks_for_another_attempt(verdicts, expected):
    assert rerun_requested(_critiques(**verdicts), list(P3)) == expected


def _loop_with(verdict_sequence: list[dict[str, str]], monkeypatch) -> list[Any]:
    """Drive the real loop, scripting what the Verifier records each attempt."""
    import importlib

    mod = importlib.import_module(
        "aaa.agents.tier1.phases.verification.run_phase_with_verification")
    attempts: list[Any] = []
    scripted = iter(verdict_sequence)
    last = verdict_sequence[-1]

    async def _fake_run(agent, dispatch, state, timeout=180):
        attempts.append(dict(dispatch))
        return {"confidence": 0.9}, state

    async def _fake_verify(verifier, agent, dispatch, state, tid_articles,
                           phase_label, confidence, rerun_count):
        verdicts = next(scripted, last)
        state["verifier_critiques"] = {tid: {"verdict": v} for tid, v in verdicts.items()}
        return max(verdicts.values(), key=lambda v: ["accept", "accept_with_notes",
                                                     "unverified", "rerun",
                                                     "escalate_hitl"].index(v))

    monkeypatch.setattr(mod, "run_agent_on_state", _fake_run)
    monkeypatch.setattr(mod, "_verify_artefacts", _fake_verify)
    monkeypatch.setattr(mod, "_get_verifier", lambda _rag=None: object())

    class _Agent:
        name, store, rag = "ModelValidator", None, None

    asyncio.run(mod.run_phase_with_verification(
        _Agent(), {"phase_id": "P3"}, {"verifier_critiques": {}}, P3, "Phase 3"))
    return attempts


def test_the_phase_reruns_for_the_artefact_the_verifier_sent_back(monkeypatch):
    """The run's own case: this used to close after one attempt and escalate."""
    attempts = _loop_with([{T09: "escalate_hitl", T11: "rerun"},
                           {T09: "escalate_hitl", T11: "accept"}], monkeypatch)

    assert len(attempts) == 2
    assert attempts[1]["rerun_context"]["attempt"] == 1
    rejected = {r["template_id"] for r in attempts[1]["rerun_context"]["rejected_artefacts"]}
    assert rejected == {T09, T11}, "the rerun carries every artefact still rejected"


def test_the_rerun_budget_still_bounds_it(monkeypatch):
    attempts = _loop_with([{T09: "escalate_hitl", T11: "rerun"}], monkeypatch)

    assert len(attempts) == 1 + MAX_RERUNS


def test_a_clean_phase_runs_once(monkeypatch):
    attempts = _loop_with([{T09: "accept", T11: "accept_with_notes"}], monkeypatch)

    assert len(attempts) == 1


# ── the Orchestrator no longer owns re-dispatch ──────────────────────────────

def _delivered(phase_artefact: str) -> dict:
    return {"phase_artefacts": {phase_artefact: {"uri": "minio://x/a"}},
            "compliance_matrix": {"Art.9": "PASS"}}


def test_a_phase_that_delivered_is_not_re_dispatched():
    """907 s of duplicated work, with no rerun_context to show for it."""
    state = _delivered("T09_model_card")
    history = [{"action": "DISPATCH", "phase_id": "P3"}]

    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P3"), state, history)

    assert out.action != "DISPATCH" or out.phase_id != "P3"
    assert note is not None and "phase's own verification loop" in note


def test_a_phase_that_delivered_nothing_is_still_the_orchestrator_s():
    """The division only holds if the other half is left alone."""
    state = {"compliance_matrix": {}}
    # Not a repeat of the previous turn: F8's no-progress guard owns that case,
    # and this test is about the new one.
    history = [{"action": "PLAN"}]

    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P3"), state, history)

    assert (out.action, out.phase_id) == ("DISPATCH", "P3")
    assert note is None


def test_the_redirect_goes_to_outstanding_work_before_closing():
    state = _delivered("T09_model_card")
    # Only phases the CSP plan marks "M" are owed.
    state["phase_plan"] = {"P1": "M", "P3": "M"}

    out, _ = apply_guards(Decision(action="DISPATCH", phase_id="P3"), state, [])

    # P1 has produced nothing, so the ladder owes it before the matrix.
    assert (out.action, out.phase_id) == ("DISPATCH", "P1")


def test_a_finished_audit_redirects_to_finalize():
    state = {"phase_artefacts": {a: {"uri": "u"} for a in (
        "T02_system_card", "T06_datasheet_for_datasets", "T09_model_card",
        "T12_output_fairness_report", "T14_governance_findings")},
        "compliance_matrix": {"Art.9": "PASS"}}

    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P3"), state, [])

    assert out.action == "FINALIZE"
    assert note is not None


def test_the_close_out_dispatch_of_p6_is_untouched():
    """`DISPATCH P6` *is* the close-out; the finalize gates own that path."""
    state = {"phase_artefacts": {a: {"uri": "u"} for a in (
        "T02_system_card", "T06_datasheet_for_datasets", "T09_model_card",
        "T12_output_fairness_report", "T14_governance_findings")},
        "compliance_matrix": {"Art.9": "PASS"}}

    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P6"), state, [])

    assert (out.action, out.phase_id) == ("DISPATCH", "P6")
    assert note is None


def test_the_dispatch_cap_still_outranks_the_new_guard():
    state = _delivered("T09_model_card")
    history = [{"action": "DISPATCH", "phase_id": "P3"}] * _PHASE_CAP

    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P3"), state, history)

    assert out.action == "ASSEMBLE_MATRIX"
    assert note is not None and "dispatch" in note
