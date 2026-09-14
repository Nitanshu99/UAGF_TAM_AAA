"""Finding F3 — the Orchestrator must observe the report, the critique and the reason.

In the assessed run every envelope read ``latest_report: None``,
``latest_critique: None`` and carried no ``hitl_reason`` at all, while
``hitl_required`` was ``true``.  The model was told an exception had been raised
and denied the exception, and spent 22 of 24 turns (~570 s, ~119,000 tokens,
zero state changes) emitting no-op ``PLAN``s while narrating a pause it had no
token to perform.

These tests pin the observation channel end to end: the verification loop records
what a phase produced, the envelope carries it, and no future call site can drop
it back to ``None``.
"""
from __future__ import annotations

import ast
import asyncio
import importlib
from pathlib import Path

from aaa.agents.tier1.orchestrator.react.summary import build_envelope
from aaa.agents.tier1.phases.verification.phase_outcome import record_phase_outcome

#: The critique the Verifier actually returned at call #005 / #010.
_CALL_005_ISSUE = {
    "field": "composition.num_instances",
    "severity": "critical",
    "materiality": "material",
    "description": "Field value is 0 but artefact.description and "
                   "declaration_summary both state 1000 instances.",
    "recommendation": "Set num_instances = 1000.",
}

_MINOR_ISSUE = {
    "field": "maintenance.update_plan",
    "severity": "minor",
    "description": "States 'Not documented — to be addressed in remediation'.",
    "recommendation": "Provide a concrete update schedule.",
}


def _critiques() -> dict:
    return {
        "T06_datasheet_for_datasets": {
            "verdict": "escalate_hitl", "total_score": 4,
            "issues": [_CALL_005_ISSUE, _MINOR_ISSUE],
        },
        "T07_data_quality_report": {"verdict": "accept_with_notes", "issues": []},
    }


# --------------------------------------------------------------------------- #
# record_phase_outcome
# --------------------------------------------------------------------------- #

def test_outcome_records_the_report_and_the_deciding_critique():
    """Both halves of the observation come out of one recording call."""
    state: dict = {"verifier_critiques": _critiques()}
    record_phase_outcome(
        state, {"summary": "Awaiting regulatory text retrieval.", "confidence": 0.3,
                "artefact_uri": "minio://eng/phase_2/T06.json"},
        ["T06_datasheet_for_datasets", "T07_data_quality_report"],
        phase_id="P2", phase_label="Phase 2 DataAuditor",
        worst="escalate_hitl", rerun_count=1)

    assert state["latest_report"]["produced"] is True
    assert state["latest_report"]["confidence"] == 0.3
    assert state["latest_report"]["phase_id"] == "P2"

    crit = state["latest_critique"]
    assert crit["worst_verdict"] == "escalate_hitl"
    assert crit["reruns_used"] == 1
    t06 = next(a for a in crit["artefacts"]
               if a["template_id"] == "T06_datasheet_for_datasets")
    assert t06["verdict"] == "escalate_hitl"
    assert t06["blocking_issues"][0]["recommendation"] == "Set num_instances = 1000."


def test_outcome_keeps_only_blocking_issues():
    """Editorial findings must not crowd out the ones a re-dispatch turns on."""
    state: dict = {"verifier_critiques": _critiques()}
    record_phase_outcome(state, {}, ["T06_datasheet_for_datasets"],
                         phase_id="P2", phase_label="Phase 2",
                         worst="escalate_hitl", rerun_count=0)

    issues = state["latest_critique"]["artefacts"][0]["blocking_issues"]
    assert [i["severity"] for i in issues] == ["critical"]


def test_outcome_caps_issues_and_trims_long_text():
    """The envelope is re-sent every turn, so it never carries a whole artefact."""
    state: dict = {"verifier_critiques": {"T06": {
        "verdict": "rerun",
        "issues": [{"severity": "major", "field": f"f{i}",
                    "description": "x" * 900, "recommendation": "y"}
                   for i in range(9)],
    }}}
    record_phase_outcome(state, {"summary": "s" * 2000}, ["T06"],
                         phase_id="P2", phase_label="Phase 2",
                         worst="rerun", rerun_count=0)

    issues = state["latest_critique"]["artefacts"][0]["blocking_issues"]
    assert len(issues) == 4
    assert len(issues[0]["description"]) < 400
    assert len(state["latest_report"]["summary"]) < 700


def test_outcome_marks_a_phase_that_produced_nothing():
    """A failed phase must not leave the previous phase's report standing."""
    state: dict = {"verifier_critiques": {},
                   "latest_report": {"phase_id": "P1", "produced": True},
                   "latest_critique": {"phase_id": "P1"}}
    record_phase_outcome(state, None, ["T09_model_card"], phase_id="P3",
                         phase_label="Phase 3", worst=None, rerun_count=0)

    assert state["latest_report"]["phase_id"] == "P3"
    assert state["latest_report"]["produced"] is False
    assert state["latest_critique"] is None


# --------------------------------------------------------------------------- #
# build_envelope
# --------------------------------------------------------------------------- #

def test_envelope_carries_the_hitl_reason():
    """`hitl_required: true` with no reason is what the model had to guess from."""
    state = {"engagement_id": "eng-01_finclear_gmbh", "hitl_required": True,
             "hitl_reason": "Phase 2 DataAuditor: Verifier verdict 'escalate_hitl' "
                            "on artefact(s) after 1 rerun(s)."}
    summary = build_envelope(state, [])["audit_state_summary"]

    assert summary["hitl_required"] is True
    assert "escalate_hitl" in summary["hitl_reason"]


def test_envelope_carries_the_report_and_critique():
    """What the verification loop recorded is what the model is handed."""
    state: dict = {"engagement_id": "eng", "verifier_critiques": _critiques()}
    record_phase_outcome(state, {"summary": "done", "confidence": 0.3},
                         ["T06_datasheet_for_datasets"], phase_id="P2",
                         phase_label="Phase 2", worst="escalate_hitl", rerun_count=1)

    envelope = build_envelope(state, [])
    assert envelope["latest_report"]["phase_id"] == "P2"
    assert envelope["latest_critique"]["worst_verdict"] == "escalate_hitl"


def test_envelope_is_empty_before_any_phase_has_run():
    """A fresh engagement observes null, not a stale neighbour's report."""
    from aaa.agents.tier1.phases.initial_state import build_initial_state

    envelope = build_envelope(build_initial_state("eng-t", {"stage_a": {}}), [])
    assert envelope["latest_report"] is None
    assert envelope["latest_critique"] is None
    assert envelope["audit_state_summary"]["hitl_reason"] is None


def test_build_envelope_has_no_argument_the_loop_fails_to_supply():
    """The F3 regression: the fields existed but no call site ever passed them.

    Asserted structurally rather than by value so that *adding* an unsupplied
    optional parameter fails here too, which is exactly how F3 arose.
    """
    loop_src = Path(importlib.import_module(
        "aaa.agents.tier1.orchestrator.react.loop").__file__).read_text("utf-8")
    calls = [n for n in ast.walk(ast.parse(loop_src))
             if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "build_envelope"]
    assert calls, "the ReAct loop no longer builds an envelope"

    import inspect
    params = list(inspect.signature(build_envelope).parameters)
    for call in calls:
        supplied = len(call.args) + len(call.keywords)
        assert supplied == len(params), (
            f"build_envelope takes {params} but the loop supplies {supplied} "
            "argument(s) — an unsupplied field silently observes as None (F3)")


# --------------------------------------------------------------------------- #
# end to end through the real verification loop
# --------------------------------------------------------------------------- #

def test_phase_escalation_reaches_the_next_envelope(monkeypatch):
    """Replay of the livelock's opening condition (calls #012 → #013).

    Phase 2 closes ``escalate_hitl``; the next Orchestrator turn must be able to
    see *what* was escalated and *why*, not just that something was.
    """
    mod = importlib.import_module(
        "aaa.agents.tier1.phases.verification.run_phase_with_verification")

    class _Agent:
        name = "DataAuditor"
        store = None

    async def _fake_run(agent, dispatch, state, timeout=180):
        return {"summary": "Awaiting regulatory text retrieval for Art. 10.",
                "confidence": 0.3}, state

    async def _fake_verify(verifier, agent, dispatch, state, tid_articles,
                           phase_label, confidence, rerun_count):
        state["verifier_critiques"] = _critiques()
        return "escalate_hitl"

    monkeypatch.setattr(mod, "run_agent_on_state", _fake_run)
    monkeypatch.setattr(mod, "_verify_artefacts", _fake_verify)
    monkeypatch.setattr(mod, "_get_verifier", lambda _rag=None: object())

    state: dict = {"engagement_id": "eng-01_finclear_gmbh", "verifier_critiques": {}}
    dispatch = {"phase_id": "P2", "evidence_uris": [], "declaration_summary": {}}
    asyncio.run(mod.run_phase_with_verification(
        _Agent(), dispatch, state,
        {"T06_datasheet_for_datasets": ["Art.10"],
         "T07_data_quality_report": ["Art.10"]},
        "Phase 2 DataAuditor"))

    envelope = build_envelope(state, [])
    assert envelope["audit_state_summary"]["hitl_required"] is True
    assert "escalate_hitl" in envelope["audit_state_summary"]["hitl_reason"], (
        "the model must not have to guess why the audit paused")
    assert envelope["latest_report"]["phase_id"] == "P2"
    assert envelope["latest_critique"]["worst_verdict"] == "escalate_hitl"
    rendered = str(envelope["latest_critique"])
    assert "composition.num_instances" in rendered
    assert "Set num_instances = 1000." in rendered
