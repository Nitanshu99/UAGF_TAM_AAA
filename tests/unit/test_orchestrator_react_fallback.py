"""ReAct loop fallback paths: malformed decisions and provider failures.

Fix 45 (finding R13) moved the threshold. A single failed decision used to end
LLM-driven sequencing for the whole engagement — in case 04 a 503 on **turn 5 of
24** — so the remaining four phases ran in a fixed code-chosen order. The decide
call is idempotent, so a failure now costs *that turn*; two in a row still ends
the loop, because at that point there is no model to steer with.
"""
from __future__ import annotations

from typing import Any

import pytest

from aaa.agents.tier1.orchestrator.react import act as act_mod
from aaa.agents.tier1.orchestrator.react import loop as loop_mod
from aaa.agents.tier1.orchestrator.react import turn as turn_mod
from aaa.agents.tier1.orchestrator.react.wrapup import BUDGET_EXHAUSTED, DECISION_FAILED
from tests.unit.support.react_helpers import FakeOrchestrator, stub_runners


def _patch_wrapup(monkeypatch, called: dict[str, Any]) -> None:
    """Replace the deterministic wrap-up with a recording stub."""
    async def fake_wrapup(agents: Any, state: dict, history: list,
                          reason: str = BUDGET_EXHAUSTED) -> dict:
        called["yes"] = True
        called["reason"] = reason
        called["turns"] = len(history)
        state["react_decision_history"] = history
        return state
    monkeypatch.setattr(loop_mod, "node_stage0", lambda s: s)
    monkeypatch.setattr(loop_mod, "deterministic_wrapup", fake_wrapup)


def _ready() -> dict[str, Any]:
    """A state FINALIZE can legitimately close: the matrix guard is satisfied."""
    return {"engagement_id": "eng-t", "compliance_matrix": {"Art.5": "PASS"}}


def _failing(times: int, then: list[dict[str, Any]] | None = None):
    """A `decide` that raises *times* times, then replays *then*."""
    calls = {"n": 0}
    queue = list(then or [])

    async def _decide(*_: Any, **__: Any) -> Any:
        calls["n"] += 1
        if calls["n"] <= times:
            raise RuntimeError("provider down")
        from aaa.agents.tier1.orchestrator.react.decisions import Decision
        return Decision(**queue.pop(0))
    return _decide, calls


# --------------------------------------------------------------------------- #
# one failure costs a turn
# --------------------------------------------------------------------------- #

async def test_one_failed_decision_costs_a_turn_not_the_loop(monkeypatch):
    """R13: turn 5 of a 24-turn budget failed and took the other 19 with it."""
    order: list[str] = []
    called: dict[str, Any] = {}
    _patch_wrapup(monkeypatch, called)
    monkeypatch.setattr(act_mod, "RUNNERS", stub_runners(order))
    decide, calls = _failing(1, [{"action": "FINALIZE", "rationale": "done"}])
    monkeypatch.setattr(loop_mod, "decide", decide)

    state = await loop_mod.run_react(object(), {}, _ready())

    assert calls["n"] == 2, "the loop asked again after the failure"
    assert called.get("yes") is None, "it reached FINALIZE, so no wrap-up"
    assert order == ["P6"]
    history = state["react_decision_history"]
    assert history[0]["action"] == turn_mod.DECISION_FAILED_ACTION
    assert history[-1]["action"] == "FINALIZE"


async def test_the_failed_turn_is_on_the_record(monkeypatch):
    """A turn that failed is a turn that happened; the next envelope says so."""
    called: dict[str, Any] = {}
    _patch_wrapup(monkeypatch, called)
    monkeypatch.setattr(act_mod, "RUNNERS", stub_runners([]))
    decide, _ = _failing(1, [{"action": "FINALIZE", "rationale": "done"}])
    monkeypatch.setattr(loop_mod, "decide", decide)

    state = await loop_mod.run_react(object(), {}, _ready())
    failed = state["react_decision_history"][0]
    assert failed["turn"] == 0
    assert "provider down" in failed["rationale"]
    assert failed["outcome"]["new_artefacts"] == []


async def test_a_later_success_clears_the_failure_count(monkeypatch):
    """Two failures separated by a good turn are not two in a row."""
    called: dict[str, Any] = {}
    _patch_wrapup(monkeypatch, called)
    monkeypatch.setattr(act_mod, "RUNNERS", stub_runners([]))
    calls = {"n": 0}

    async def _decide(*_: Any, **__: Any) -> Any:
        from aaa.agents.tier1.orchestrator.react.decisions import Decision
        calls["n"] += 1
        if calls["n"] in (1, 3):
            raise RuntimeError("provider down")
        if calls["n"] == 2:
            return Decision(action="ASSEMBLE_MATRIX", rationale="matrix")
        return Decision(action="FINALIZE", rationale="done")
    monkeypatch.setattr(loop_mod, "decide", _decide)
    monkeypatch.setattr(act_mod, "node_compliance_matrix", lambda s: s)
    monkeypatch.setattr(act_mod, "node_hitl_checkpoint", lambda s: s)

    await loop_mod.run_react(object(), {}, _ready())
    assert calls["n"] == 4
    assert called.get("yes") is None


# --------------------------------------------------------------------------- #
# two in a row still ends it
# --------------------------------------------------------------------------- #

async def test_two_consecutive_failures_end_the_loop(monkeypatch):
    called: dict[str, Any] = {}
    _patch_wrapup(monkeypatch, called)
    decide, calls = _failing(9)
    monkeypatch.setattr(loop_mod, "decide", decide)

    await loop_mod.run_react(object(), {}, _ready())

    assert calls["n"] == turn_mod.MAX_DECISION_FAILURES == 2
    assert called["yes"] is True
    assert called["reason"] == DECISION_FAILED
    assert called["turns"] == 2, "both failed turns are on the record"


async def test_the_reason_distinguishes_a_dead_model_from_a_spent_budget(monkeypatch):
    """`react_termination.reason` had one string for two different facts."""
    assert DECISION_FAILED != BUDGET_EXHAUSTED
    called: dict[str, Any] = {}
    _patch_wrapup(monkeypatch, called)
    monkeypatch.setattr(loop_mod, "MAX_TURNS", 1)
    monkeypatch.setattr(act_mod, "node_plan", lambda s: s)

    async def _plan(*_: Any, **__: Any) -> Any:
        from aaa.agents.tier1.orchestrator.react.decisions import Decision
        return Decision(action="PLAN", rationale="plan the phases")
    monkeypatch.setattr(loop_mod, "decide", _plan)

    await loop_mod.run_react(object(), {}, _ready())
    assert called["reason"] == BUDGET_EXHAUSTED, (
        "a loop that ran out of turns must not read as one whose model died")
    assert called["turns"] == 1


async def test_a_malformed_decision_is_retried_then_refused(monkeypatch):
    """A DecisionError is a failed turn like any other."""
    called: dict[str, Any] = {}
    order: list[str] = []
    _patch_wrapup(monkeypatch, called)
    monkeypatch.setattr(act_mod, "RUNNERS", stub_runners(order))
    orch = FakeOrchestrator([{"action": "NONSENSE"}, {"action": "NONSENSE"}])

    state = await loop_mod.run_react(orch, {}, _ready())

    assert called.get("yes") is True
    assert called["reason"] == DECISION_FAILED
    assert not order, "nothing dispatched on an invalid decision"
    assert "react_decision_history" in state


@pytest.mark.parametrize("action", ["DECISION_FAILED"])
def test_the_failed_turn_is_not_one_of_the_models_actions(action):
    """`_dispatch_count` and the no-progress guard both read this history."""
    from aaa.agents.tier1.orchestrator.react.decisions import ACTIONS
    assert turn_mod.DECISION_FAILED_ACTION == action
    assert action not in ACTIONS
