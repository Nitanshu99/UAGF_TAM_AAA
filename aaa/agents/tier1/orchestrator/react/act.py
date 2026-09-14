"""Executing one decided ReAct action, and recording the turn it produced."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.decisions import Decision
from aaa.agents.tier1.orchestrator.react.escalate import record_escalation
from aaa.agents.tier1.orchestrator.react.runners_map import RUNNERS
from aaa.agents.tier1.orchestrator.react.summary import _admitted, turn_outcome
from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.node_stubs import node_hitl_checkpoint
from aaa.agents.tier1.phases.nodes.plan import node_plan


async def act_on(decision: Decision, agents: dict[str, Any], state: dict,
                 history: list[dict[str, Any]], turn: int, note: str | None,
                 asked: dict[str, Any]) -> tuple[dict, bool]:
    """Execute *decision* and append the turn to *history*.

    :param decision: The decision as the guards left it.
    :param agents: Agent registry from ``initialise_agents``.
    :param state: The AuditState dict.
    :param history: Append-only decision/outcome log, extended in place.
    :param turn: The turn number.
    :param note: The guard override note, when a guard corrected the decision.
    :param asked: What the model proposed, kept only when a guard overrode it.
    :returns: ``(state, closed)`` — *closed* is ``True`` when this turn was the
        FINALIZE that ends the audit.
    """
    before = _admitted(state)
    if decision.action == "PLAN":
        state = node_plan(state)
    elif decision.action == "DISPATCH" and decision.phase_id != "P6":
        state = await RUNNERS[decision.phase_id or ""](agents, state)
    elif decision.action == "ESCALATE_HITL":
        # Records the alert; the audit is not paused — HITL engagements close
        # with a provisional report plus a review packet. (F8)
        state = record_escalation(state, decision.rationale)
    elif decision.action == "ASSEMBLE_MATRIX":
        state = node_hitl_checkpoint(node_compliance_matrix(state))
    else:  # FINALIZE or DISPATCH P6 — emit the report and stop.
        state = await RUNNERS["P6"](agents, state)
        history.append({"turn": turn, "action": "FINALIZE",
                        "rationale": decision.rationale, "guard_override": note,
                        **asked})
        return state, True
    history.append({"turn": turn, "action": decision.action,
                    "phase_id": decision.phase_id, "rationale": decision.rationale,
                    "guard_override": note, "outcome": turn_outcome(state, before),
                    **asked})
    return state, False


__all__ = ["act_on"]
