"""Fix 35 — a phase that produced no report must not deliver silent stubs (R2, R3).

Case 01's Phase 1 is the fixture throughout: a 216.8 s ScopeAgent reply discarded
by a 120 s budget, after which ``node_phase1_stub`` wrote T02–T05 with synthetic
``mem://`` URIs and manufactured ``accept_with_notes`` critiques — an *admitting*
verdict — while nothing recorded that the phase had failed.
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest

from aaa.agents.tier1.orchestrator.react.coverage import phase_has_run
from aaa.agents.tier1.phases.verification.no_report import (
    NO_REPORT,
    gate_on_no_report,
    record_phase_failure,
)
from aaa.agents.tier1.phases.verification.unadmitted import gate_on_unadmitted
from aaa.platform.state.admission import admitted_artefacts

P1_TIDS: dict[str, list[str]] = {
    "T02_system_card": ["Art.5", "Art.13"],
    "T03_annex_iii_mapping": ["Art.6", "Annex_III"],
    "T04_risk_tier_decision": ["Art.5", "Art.6"],
    "T05_art43_decision": ["Art.43"],
}
P1_ARTICLES = ["Annex_III", "Art.13", "Art.43", "Art.5", "Art.6"]


def _state() -> dict:
    return {"engagement_id": "eng-01", "phase_artefacts": {}, "verifier_critiques": {}}


def _gate(state: dict, tids: dict[str, list[str]] | None = None) -> list[str]:
    return gate_on_no_report(state, tids or P1_TIDS,
                             phase_id="P1", phase_label="Phase 1 ScopeAgent")


# --------------------------------------------------------------------------- #
# a timed-out phase produces no artefact, and its articles are held
# --------------------------------------------------------------------------- #

def test_the_articles_are_unevidenced_rather_than_silent():
    state = _state()
    assert _gate(state) == P1_ARTICLES
    assert state["insufficient_evidence_articles"] == P1_ARTICLES


def test_no_artefact_is_written_in_the_phases_place():
    state = _state()
    _gate(state)
    assert state["phase_artefacts"] == {}
    assert state["verifier_critiques"] == {}
    assert admitted_artefacts(state) == set()


def test_phase_has_run_agrees_with_reality():
    """R3: the stub made `phase_has_run("P1")` answer yes to a phase that failed."""
    state = _state()
    _gate(state)
    assert phase_has_run("P1", state, []) is False


def test_the_engagement_is_flagged_for_human_review():
    state = _state()
    _gate(state)
    assert state["hitl_required"] is True


# --------------------------------------------------------------------------- #
# the finding names the phase, the cause and the articles
# --------------------------------------------------------------------------- #

def _finding(state: dict) -> dict:
    return next(f for f in state["blocking_findings"]
                if f["finding_id"] == "P1-VERIFY-NOREPORT")


def test_a_budget_loss_says_it_was_the_budget():
    state = _state()
    record_phase_failure(state, "ScopeAgent", 216.8, 120.0,
                         TimeoutError("worker abandoned"))
    _gate(state)
    finding = _finding(state)
    assert "abandoned at its 120s budget" in finding["description"]
    assert set(finding["eu_ai_act_articles"]) == set(P1_ARTICLES)
    assert "Phase 1 ScopeAgent" in finding["description"]
    assert "T02_system_card" in finding["description"]


def test_a_provider_failure_says_it_was_the_provider():
    """Case 03 #004 — a 503, not a timeout, and a reader must be able to tell."""
    class _ServiceUnavailableError(Exception):
        pass

    state = _state()
    record_phase_failure(state, "ScopeAgent", 182.0, 300.0,
                         _ServiceUnavailableError("Service temporarily overloaded"))
    _gate(state)
    assert "the provider failed after 182.0s" in _finding(state)["description"]


def test_an_ordinary_error_is_reported_as_itself():
    state = _state()
    record_phase_failure(state, "ScopeAgent", 3.0, 300.0, ValueError("bad contract"))
    _gate(state)
    assert "bad contract" in _finding(state)["description"]


def test_the_failure_record_is_consumed_not_left_behind():
    state = _state()
    record_phase_failure(state, "ScopeAgent", 216.8, 120.0, TimeoutError("x"))
    _gate(state)
    assert "_last_phase_failure" not in state


# --------------------------------------------------------------------------- #
# the gate is two-way: a re-dispatch that delivers releases what the loss held
# --------------------------------------------------------------------------- #

def test_a_later_successful_attempt_releases_the_articles():
    """Case 01 re-dispatched three lost phases; attempt 2's success must count."""
    state = _state()
    _gate(state)
    assert state["insufficient_evidence_articles"] == P1_ARTICLES

    for tid in P1_TIDS:
        state["phase_artefacts"][tid] = {"uri": f"minio://x/{tid}"}
        state["verifier_critiques"][tid] = {"verdict": "accept"}
    gate_on_unadmitted(state, P1_TIDS, phase_id="P1", phase_label="Phase 1 ScopeAgent")

    assert state["insufficient_evidence_articles"] == []
    assert state["unadmitted_artefacts"] == []
    assert not [f for f in state.get("blocking_findings") or []
                if f["finding_id"] == "P1-VERIFY-NOREPORT"]


def test_a_second_loss_replaces_the_first_rather_than_stacking():
    state = _state()
    _gate(state)
    _gate(state)
    assert len(state["unadmitted_artefacts"]) == len(P1_TIDS)
    assert len([f for f in state["blocking_findings"]
                if f["finding_id"] == "P1-VERIFY-NOREPORT"]) == 1


def test_the_entries_sit_beside_the_real_unadmitted_verdicts():
    """One list, so the matrix and the T18 manifest need to know about one."""
    state = _state()
    _gate(state)
    assert {e["verdict"] for e in state["unadmitted_artefacts"]} == {NO_REPORT}
    assert {e["phase_id"] for e in state["unadmitted_artefacts"]} == {"P1"}


def test_another_phases_record_is_left_alone():
    state = _state()
    gate_on_no_report(state, {"T14_governance_findings": ["Art.9"]},
                      phase_id="P5", phase_label="Phase 5 GovernanceAgent")
    _gate(state)
    assert {e["phase_id"] for e in state["unadmitted_artefacts"]} == {"P1", "P5"}
    assert "Art.9" in state["insufficient_evidence_articles"]


# --------------------------------------------------------------------------- #
# the stub keeps its real job, and loses the one it was pretending to
# --------------------------------------------------------------------------- #


def _runner_path(runner: str) -> str:
    """The source file of a runner: ``phase_N`` lives in ``phase/pN.py`` since the family fold."""
    if runner.startswith("phase_"):
        return f"aaa/agents/tier1/phases/phase_runners/phase/p{runner[-1]}.py"
    return f"aaa/agents/tier1/phases/phase_runners/{runner}.py"


@pytest.mark.parametrize("runner", ["phase_1", "phase_5", "phase_6", "uagf_tam_l"])
def test_no_runner_stubs_the_no_report_path(runner):
    """The four that still did. Phases 2-4 already returned bare state."""
    from pathlib import Path
    src = Path(_runner_path(runner)).read_text()
    after = src.split("if report is None:", 1)[1].split("return", 1)[0] + \
        src.split("if report is None:", 1)[1].split("return", 1)[1].split("\n", 1)[0]
    assert "stub" not in after.replace("# Fix 35", "").split("\n")[-1]


@pytest.mark.parametrize("runner", ["phase_1", "phase_5", "phase_6", "uagf_tam_l"])
def test_the_unwired_path_still_stubs(runner):
    """No dispatch was attempted, so a deterministic placeholder is honest there."""
    from pathlib import Path
    src = Path(_runner_path(runner)).read_text()
    unwired = src.split("if agent is None:", 1)[1].split("\n")[1]
    assert "stub(state)" in unwired


def test_a_phase_that_succeeds_is_completely_unaffected():
    """Acceptance: nothing on the success path changed."""
    state = _state()
    for tid in P1_TIDS:
        state["phase_artefacts"][tid] = {"uri": f"minio://x/{tid}"}
        state["verifier_critiques"][tid] = {"verdict": "accept"}
    gate_on_unadmitted(state, P1_TIDS, phase_id="P1", phase_label="Phase 1 ScopeAgent")
    assert state.get("insufficient_evidence_articles") in (None, [])
    assert "unadmitted_artefacts" not in state
    assert "hitl_required" not in state
    assert phase_has_run("P1", state, []) is True


# --------------------------------------------------------------------------- #
# end to end through the runner
# --------------------------------------------------------------------------- #

class _FailingAgent:
    name = "ScopeAgent"

    async def process(self, message: Any) -> Any:
        raise TimeoutError("worker abandoned at its budget")


def test_the_no_report_path_runs_the_gate():
    from aaa.agents.tier1.phases.verification import run_phase_with_verification

    state = _state()
    dispatch = {"phase_id": "P1"}
    report, state = asyncio.run(run_phase_with_verification(
        _FailingAgent(), dispatch, state, tid_articles=P1_TIDS,
        phase_label="Phase 1 ScopeAgent", timeout=1))

    assert report is None
    assert state["phase_artefacts"] == {}
    assert state["insufficient_evidence_articles"] == P1_ARTICLES
    assert state["latest_report"]["produced"] is False
    assert _finding(state)["finding_id"] == "P1-VERIFY-NOREPORT"


def test_the_gate_runs_before_the_return():
    """Structural: R2 was entirely 'the return came first'.

    Followed across the one hop the no-report branch now makes: the loop calls
    ``record_lost_attempt`` before it returns, and that records the outcome and
    runs the gate before *it* returns.
    """
    from aaa.agents.tier1.phases.verification import run_phase_with_verification
    from aaa.agents.tier1.phases.verification.lost_attempt import record_lost_attempt

    src = inspect.getsource(run_phase_with_verification)
    body = src.split("if report is None:", 1)[1].split("return None, state", 1)[0]
    assert "record_lost_attempt" in body

    recorded = inspect.getsource(record_lost_attempt)
    assert "gate_on_no_report" in recorded
    assert recorded.index("record_phase_outcome") < recorded.index("gate_on_no_report(")
