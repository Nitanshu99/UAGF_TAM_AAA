"""Termination helpers for the ReAct loop.

``stamp`` records the decision history on the final state; the deterministic
wrap-up runs when the turn budget is exhausted or a decision failed twice —
always logged, matching PROMPT.md's labelled-fallback constraint.

Fix 45 (finding R13) split that "or". The two causes had one reason string,
``"turn budget exhausted or decision failure"``, and a reader of
``react_termination`` could not tell an audit that ran out of turns from one
that lost its model — which in case 04 was a **503 on turn 5 of 24**. They are
different facts about an engagement and they call for different responses.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.orchestrator.react.assembled import matrix_assembled
from aaa.agents.tier1.orchestrator.react.rescue import run_outstanding
from aaa.agents.tier1.orchestrator.react.runners_map import RUNNERS
from aaa.agents.tier1.orchestrator.react.unevidenced import mark_unevidenced
from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.node_stubs import node_hitl_checkpoint

logger = logging.getLogger(__name__)

__all__ = ["BUDGET_EXHAUSTED", "DECISION_FAILED", "deterministic_wrapup", "stamp"]


def stamp(state: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach the auditable decision history to the final state.

    :param state: Final AuditState dict.
    :type state: dict[str, Any]
    :param history: Append-only decision/outcome log.
    :type history: list[dict[str, Any]]
    :returns: The same state, with ``react_decision_history`` set.
    :rtype: dict[str, Any]
    """
    state["react_decision_history"] = history
    return state


#: The loop ran every turn it had and never reached FINALIZE.
BUDGET_EXHAUSTED = "turn budget exhausted"

#: Two consecutive decision calls failed, so there is no model to steer with.
DECISION_FAILED = "decision failed twice in a row"


async def deterministic_wrapup(agents: dict[str, Any], state: dict[str, Any],
                               history: list[dict[str, Any]],
                               reason: str = BUDGET_EXHAUSTED) -> dict[str, Any]:
    """Assemble the matrix (if missing) and emit the report deterministically.

    :param agents: Agent registry from ``initialise_agents``.
    :type agents: dict[str, Any]
    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :param history: Append-only decision/outcome log.
    :type history: list[dict[str, Any]]
    :param reason: Why the loop ended — :data:`BUDGET_EXHAUSTED` or
        :data:`DECISION_FAILED`. Recorded verbatim in ``react_termination``.
    :type reason: str
    :returns: Final state after Phase 6.
    :rtype: dict[str, Any]
    """
    turns_used = len(history)
    logger.warning("ReAct loop ended (%s); deterministic wrap-up after %d turn(s) — "
                   "running any mandatory phase the loop did not reach.",
                   reason, turns_used)
    # F12: forcing the outstanding phases must precede marking, or the wrap-up
    # records as "could not be assessed" work it never attempted.
    state, rescue = await run_outstanding(agents, state, history)
    # Must still precede matrix assembly: an article with no backing artefact is
    # reported PASS unless it is on the insufficient list, so whatever the rescue
    # could not produce would otherwise close claiming conformity never assessed.
    unevidenced = mark_unevidenced(state)
    # Suggestion 4 at call #013: a run that exhausted its budget was
    # indistinguishable in the *output* from one the model steered to completion.
    state["react_termination"] = {
        "mode": "deterministic_wrapup",
        "reason": reason,
        "turns_used": turns_used,
        "phases_forced": rescue["forced"],
        "phases_not_run": rescue["skipped"],
        "articles_unevidenced": unevidenced,
    }
    if not matrix_assembled(state):
        state = node_hitl_checkpoint(node_compliance_matrix(state))
    state = await RUNNERS["P6"](agents, state)
    return stamp(state, history)
