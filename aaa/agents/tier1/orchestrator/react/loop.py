"""The Orchestrator ReAct loop — observe, decide, act, repeat.

Each turn: summarise the audit state, ask the Orchestrator model for one
decision, validate it against the hard gates, execute it, and append the
decision + outcome to an auditable history that feeds the next observation.
Terminates on FINALIZE (Phase 6) or when the turn budget runs out, in which
case the matrix/finalize path is forced deterministically (logged as such).
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.orchestrator.react.act import act_on
from aaa.agents.tier1.orchestrator.react.decision_failure import record_decision_failure
from aaa.agents.tier1.orchestrator.react.guards import apply_guards
from aaa.agents.tier1.orchestrator.react.llm import decide
from aaa.agents.tier1.orchestrator.react.summary import build_envelope
from aaa.agents.tier1.orchestrator.react.turn import MAX_DECISION_FAILURES
from aaa.agents.tier1.orchestrator.react.wrapup import DECISION_FAILED, deterministic_wrapup, stamp
from aaa.agents.tier1.phases.nodes.stage0 import node_stage0

logger = logging.getLogger(__name__)

MAX_TURNS: int = 24




async def run_react(orchestrator: Any, agents: dict[str, Any], state: dict) -> dict:
    """Drive one engagement with LLM-decided sequencing.

    :param orchestrator: The :class:`Orchestrator` (model + audit logging).
    :type orchestrator: Any
    :param agents: Agent registry from ``initialise_agents``.
    :type agents: dict[str, Any]
    :param state: Initial AuditState dict.
    :type state: dict
    :returns: Final state after Phase 6.
    :rtype: dict
    """
    history: list[dict[str, Any]] = []
    failures = 0
    state = node_stage0(state)
    for turn in range(MAX_TURNS):
        try:
            decision = await decide(orchestrator, build_envelope(state, history))
        # DecisionError (malformed reply) and any provider/runtime failure are
        # absorbed: fix 45 (R13). The decide call is idempotent, so the failure
        # costs *this turn* and the next one asks again — until two in a row say
        # there is no model to steer with.
        except Exception as exc:  # noqa: BLE001
            failures += 1
            record_decision_failure(state, history, turn, exc)
            if failures >= MAX_DECISION_FAILURES:
                logger.error("ReAct turn %d: decide failed %d times in a row (%s) — "
                             "there is no model to steer with; deterministic wrap-up.",
                             turn, failures, exc)
                return await deterministic_wrapup(agents, state, history, DECISION_FAILED)
            logger.warning("ReAct turn %d: decide failed (%s). The state is unchanged "
                           "and the call is idempotent, so this costs a turn and the "
                           "loop asks again.", turn, exc)
            continue
        failures = 0
        proposed = decision
        decision, note = apply_guards(decision, state, history)
        if note:
            logger.warning("ReAct turn %d: guard override — %s", turn, note)
        # What the model *asked* for, kept only when a guard overrode it: without
        # it a corrected turn is indistinguishable from a compliant one, and the
        # no-progress guard cannot see a proposal being repeated. (F8)
        asked = ({"proposed_action": proposed.action,
                  "proposed_phase_id": proposed.phase_id} if note else {})
        state, closed = await act_on(decision, agents, state, history,
                                     turn, note, asked)
        if closed:
            return stamp(state, history)
    return await deterministic_wrapup(agents, state, history)
