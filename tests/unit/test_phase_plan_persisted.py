"""``node_plan`` must persist the phase plan the ReAct loop reads."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import pending_mandatory
from aaa.agents.tier1.phases.nodes.plan import node_plan


def _state() -> dict[str, Any]:
    """A high-risk tabular engagement the CSP solver can plan."""
    return {
        "engagement_id": "eng-plan-test",
        "risk_tier": "high",
        "modality": "tabular",
        "is_llm_or_agentic": False,
        "annex_iii_mapping": [],
        "phase_artefacts": {},
    }


def test_phase_plan_is_written_to_state() -> None:
    """The plan must survive the node, not only reach the log.

    ``node_plan`` wrote only the template-level ``phase_status``, so the ReAct
    envelope and the coverage guard — both of which read ``phase_plan`` — saw
    ``None``. The Orchestrator was told the plan was null on every turn,
    correctly kept answering PLAN, and exhausted its 24-turn budget without
    dispatching a single phase.
    """
    state = node_plan(_state())
    assert state.get("phase_plan"), "phase_plan must be persisted for the ReAct loop"
    assert state.get("phase_status"), "template-level expansion must still be written"


def test_coverage_guard_can_see_owed_phases() -> None:
    """With the plan persisted, the guard can name a mandatory phase."""
    state = node_plan(_state())
    assert pending_mandatory(state, {}, cap=2) is not None
