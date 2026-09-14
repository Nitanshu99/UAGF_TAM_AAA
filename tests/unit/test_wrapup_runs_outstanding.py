"""Finding F12 — exhausting the turn budget must not cancel the audit's work.

`deterministic_wrapup` marked the outstanding phases unevidenced, assembled the
matrix and jumped to Phase 6. On the assessed run that silently cancelled six of
eight mandatory phases — P1, P3, P4, P5, CYBER, PRIV — on a submission scoring
`intake_completeness_score = 1.0`, and the report still read
`PASS_WITH_OBSERVATIONS`.

The wrap-up path bypasses `apply_guards` entirely, so the gates the loop enforces
per turn are re-asserted here: the Art. 5 halt, the intake gate and the per-phase
dispatch cap.
"""
from __future__ import annotations

import asyncio
from typing import Any

from aaa.agents.tier1.orchestrator.react import rescue as rescue_mod
from aaa.agents.tier1.orchestrator.react import wrapup as wrapup_mod
from aaa.agents.tier1.phases.nodes.plan import PHASE_TO_TEMPLATES

#: RUNNERS keys back to the CSP plan keys they answer to.
_PLAN_KEY = {"PRIVACY": "PRIV"}

#: the assessed run's plan: everything mandatory, the L-branch skipped.
_PLAN = {"P1": "M", "P2": "M", "P3": "M", "P4": "M", "P5": "M", "P6": "M",
         "L": "S", "CYBER": "M", "PRIV": "M"}


def _state(**overrides: Any) -> dict[str, Any]:
    """State as the assessed run left it: only Phase 2 ever ran."""
    state: dict[str, Any] = {
        "engagement_id": "eng-01_finclear_gmbh",
        "intake_completeness_score": 1.0,
        "phase_plan": dict(_PLAN),
        # Phase 2 emitted its full contract, as it did in the assessed run.
        "phase_artefacts": {tid: {} for tid in PHASE_TO_TEMPLATES["P2"]},
    }
    state.update(overrides)
    return state


def _runners(order: list[str]) -> dict[str, Any]:
    """RUNNERS-shaped stubs recording call order and emitting a phase's templates.

    A real runner emits every template its phase owns (P1 alone emits four), and
    ``unevidenced_articles`` checks all of them — so a stub emitting only the
    coverage artefact would look like a phase that half-failed.
    """
    async def make(tag: str, state: dict) -> dict:
        order.append(tag)
        for tid in PHASE_TO_TEMPLATES.get(_PLAN_KEY.get(tag, tag), []):
            state.setdefault("phase_artefacts", {})[tid] = {"uri": f"minio://{tag}"}
        return state
    return {pid: (lambda a, s, t=pid: make(t, s))
            for pid in ("P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIVACY")}


def _run(state: dict, order: list[str], monkeypatch, history=None) -> dict:
    monkeypatch.setattr(rescue_mod, "RUNNERS", _runners(order))
    monkeypatch.setattr(wrapup_mod, "RUNNERS", _runners(order))
    monkeypatch.setattr(wrapup_mod, "node_compliance_matrix",
                        lambda s: {**s, "compliance_matrix": {"Art.6": "PASS"}})
    monkeypatch.setattr(wrapup_mod, "node_hitl_checkpoint", lambda s: s)
    return asyncio.run(wrapup_mod.deterministic_wrapup({}, state, history or []))


# --------------------------------------------------------------------------- #
# the rescue
# --------------------------------------------------------------------------- #

def test_wrapup_runs_the_phases_the_budget_never_reached(monkeypatch):
    """The assessed failure: six mandatory phases cancelled by a turn overrun."""
    order: list[str] = []
    final = _run(_state(), order, monkeypatch)

    forced = final["react_termination"]["phases_forced"]
    assert forced == ["P1", "P3", "P4", "P5", "CYBER", "PRIVACY"], (
        "every mandatory phase the loop did not reach must be run, not cancelled")
    assert order[-1] == "P6", "the report is still emitted last"
    assert "P2" not in forced, "a phase that already produced its artefact is not re-run"


def test_articles_are_marked_only_after_the_rescue_has_tried(monkeypatch):
    """Marking must describe what could not be produced, not what was skipped."""
    order: list[str] = []
    final = _run(_state(), order, monkeypatch)

    assert final["react_termination"]["articles_unevidenced"] == [], (
        "the rescue produced every mandatory artefact; nothing is unassessed")


def test_a_phase_that_cannot_run_is_still_marked(monkeypatch):
    """A runner that raises leaves its articles unevidenced, and says so."""
    order: list[str] = []

    async def boom(_agents, _state):
        raise RuntimeError("model provider unreachable")

    runners = _runners(order)
    runners["P5"] = boom
    monkeypatch.setattr(rescue_mod, "RUNNERS", runners)
    monkeypatch.setattr(wrapup_mod, "RUNNERS", runners)
    monkeypatch.setattr(wrapup_mod, "node_compliance_matrix",
                        lambda s: {**s, "compliance_matrix": {}})
    monkeypatch.setattr(wrapup_mod, "node_hitl_checkpoint", lambda s: s)
    final = asyncio.run(wrapup_mod.deterministic_wrapup({}, _state(), []))

    term = final["react_termination"]
    assert "P5" not in term["phases_forced"]
    assert any(s["phase"] == "P5" and "unreachable" in s["reason"]
               for s in term["phases_not_run"])
    assert "Art.9" in term["articles_unevidenced"], "P5's articles stay unevidenced"


# --------------------------------------------------------------------------- #
# the gates the wrap-up path bypasses
# --------------------------------------------------------------------------- #

def test_art5_halt_stops_the_rescue(monkeypatch):
    """A prohibited practice must not cause six phase agents to be spawned."""
    order: list[str] = []
    final = _run(_state(risk_tier="prohibited"), order, monkeypatch)

    assert final["react_termination"]["phases_forced"] == []
    assert order == ["P6"], "only the report may run under an Art. 5 halt"


def test_intake_gate_still_blocks_phase_1(monkeypatch):
    """The gate the loop enforces per turn is not waived by the fallback."""
    order: list[str] = []
    final = _run(_state(intake_completeness_score=0.5), order, monkeypatch)

    term = final["react_termination"]
    assert "P1" not in term["phases_forced"]
    assert any(s["phase"] == "P1" and "intake_completeness_score" in s["reason"]
               for s in term["phases_not_run"])


def test_a_phase_already_at_its_dispatch_cap_is_not_retried(monkeypatch):
    """A phase that failed three times is not worth a fourth attempt."""
    from aaa.agents.tier1.orchestrator.react.guards import _PHASE_CAP

    history = [{"action": "DISPATCH", "phase_id": "P3",
                "outcome": {"new_artefacts": []}} for _ in range(_PHASE_CAP)]
    order: list[str] = []
    final = _run(_state(), order, monkeypatch, history=history)

    term = final["react_termination"]
    assert "P3" not in term["phases_forced"]
    assert any(s["phase"] == "P3" and "cap" in s["reason"]
               for s in term["phases_not_run"])


def test_optional_and_skipped_phases_are_not_forced(monkeypatch):
    """Only phases the CSP plan marks M are owed."""
    order: list[str] = []
    plan = dict(_PLAN, P3="O", P4="S", CYBER="O", PRIV="S")
    final = _run(_state(phase_plan=plan), order, monkeypatch)

    forced = final["react_termination"]["phases_forced"]
    assert forced == ["P1", "P5"]


def test_l_branch_runs_before_the_phases_it_replaces(monkeypatch):
    """An agentic engagement rescues L, not P2-P4."""
    order: list[str] = []
    plan = dict(_PLAN, L="M", P2="S", P3="S", P4="S")
    final = _run(_state(phase_plan=plan, phase_artefacts={}), order, monkeypatch)

    forced = final["react_termination"]["phases_forced"]
    assert forced[:2] == ["P1", "L"]
    assert "P2" not in forced


# --------------------------------------------------------------------------- #
# visibility (suggestion 4 at call #013)
# --------------------------------------------------------------------------- #

def test_a_budget_exhausted_run_is_distinguishable_in_the_output(monkeypatch):
    """It used to be visible only in a log line."""
    order: list[str] = []
    history = [{"turn": i, "action": "PLAN", "outcome": {"new_artefacts": []}}
               for i in range(24)]
    final = _run(_state(), order, monkeypatch, history=history)

    term = final["react_termination"]
    assert term["mode"] == "deterministic_wrapup"
    assert term["turns_used"] == 24, "turns are counted before the rescue extends history"


def test_forced_phases_are_recorded_in_the_decision_history(monkeypatch):
    """A forced run must not read as a model decision."""
    order: list[str] = []
    history: list[dict[str, Any]] = []
    final = _run(_state(), order, monkeypatch, history=history)

    forced_entries = [h for h in final["react_decision_history"] if h.get("forced")]
    assert [h["phase_id"] for h in forced_entries] == [
        "P1", "P3", "P4", "P5", "CYBER", "PRIVACY"]
    assert all(h["guard_override"] for h in forced_entries)


def test_termination_reaches_the_report_architect(monkeypatch):
    """The evidence surface handed to Phase 6 must carry it."""
    from aaa.agents.tier1.phases.phase_runners.phase6_declaration_summary import (
        _phase6_declaration_summary,
    )
    order: list[str] = []
    final = _run(_state(), order, monkeypatch)
    summary = _phase6_declaration_summary(final, "eng-t", {})

    assert summary["react_termination"]["mode"] == "deterministic_wrapup"
