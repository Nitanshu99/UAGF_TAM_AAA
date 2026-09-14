"""ReAct loop behaviour with scripted decisions over stub runners."""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.react import act as act_mod
from aaa.agents.tier1.orchestrator.react import loop as loop_mod
from tests.unit.support.react_helpers import FakeOrchestrator, stub_runners


async def test_loop_follows_scripted_decisions(monkeypatch):
    """Dispatch order comes from decisions, not hardcoded edges."""
    order: list[str] = []
    monkeypatch.setattr(loop_mod, "node_stage0", lambda s: s)
    monkeypatch.setattr(act_mod, "node_plan",
                        lambda s: {**s, "phase_plan": {"P1": "M"}})
    monkeypatch.setattr(act_mod, "node_compliance_matrix",
                        lambda s: {**s, "compliance_matrix": {"Art.6": "PASS"}})
    monkeypatch.setattr(act_mod, "node_hitl_checkpoint", lambda s: s)
    monkeypatch.setattr(act_mod, "RUNNERS", stub_runners(order))
    orch = FakeOrchestrator([
        {"action": "PLAN", "rationale": "plan first"},
        {"action": "DISPATCH", "phase_id": "P1"},
        {"action": "DISPATCH", "phase_id": "P4"},   # LLM-chosen order, not DAG order
        {"action": "DISPATCH", "phase_id": "P2"},
        {"action": "ASSEMBLE_MATRIX"},
        {"action": "FINALIZE", "rationale": "report time"},
    ])
    state = await loop_mod.run_react(orch, {}, {"engagement_id": "eng-t",
                                                "intake_completeness_score": 1.0})
    assert order == ["P1", "P4", "P2", "P6"]
    history = state["react_decision_history"]
    assert [h["action"] for h in history][:5] == [
        "PLAN", "DISPATCH", "DISPATCH", "DISPATCH", "ASSEMBLE_MATRIX"]
    # each turn's envelope carried the history accumulated so far (observation feed)
    assert orch.history_lengths == [0, 1, 2, 3, 4, 5]
