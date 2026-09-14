"""The individual gate questions the guard asks of one proposed decision."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import phase_has_run
from aaa.agents.tier1.verifier import MAX_RERUNS

#: intake gate below which Phase 1 must not be dispatched (PROMPT.md).
INTAKE_GATE: float = 0.80
#: dispatches allowed per phase: the initial run plus MAX_RERUNS re-runs.
_PHASE_CAP: int = 1 + MAX_RERUNS
def _dispatch_count(history: list[dict[str, Any]], phase_id: str) -> int:
    """Count prior dispatches of *phase_id* in the decision history.

    :param history: Append-only decision/outcome log for this engagement.
    :type history: list[dict[str, Any]]
    :param phase_id: Phase identifier to count.
    :type phase_id: str
    :returns: Number of prior DISPATCH decisions targeting the phase.
    :rtype: int
    """
    return sum(1 for h in history
               if h.get("action") == "DISPATCH" and h.get("phase_id") == phase_id)
def _intake_blocks(phase_id: str | None, state: dict[str, Any]) -> bool:
    """Would the intake-completeness gate refuse to dispatch *phase_id*?

    Asked twice: once of the decision itself, and once of a phase the
    precedence gate is about to redirect to — a rewrite onto a phase another
    gate forbids would deadlock the audit on the guard's own correction.

    :param phase_id: Phase the dispatch targets.
    :type phase_id: str | None
    :param state: The AuditState dict.
    :type state: dict[str, Any]
    :returns: ``True`` when the gate blocks it.
    :rtype: bool
    """
    score = state.get("intake_completeness_score")
    return phase_id == "P1" and score is not None and float(score) < INTAKE_GATE
def _already_delivered(phase_id: str, state: dict[str, Any],
                       history: list[dict[str, Any]]) -> bool:
    """Has *phase_id* already produced the artefact it owes?

    P6 is excluded: the loop executes ``DISPATCH P6`` as the close-out, and the
    finalize gates below own that path.

    :param phase_id: Phase the dispatch targets.
    :param state: The AuditState dict.
    :param history: Append-only decision/outcome log.
    :returns: ``True`` when re-dispatching it would duplicate the phase's own
        rerun loop.
    """
    return phase_id != "P6" and phase_has_run(phase_id, state, history)


__all__ = ["INTAKE_GATE", "_PHASE_CAP", "_already_delivered", "_dispatch_count", "_intake_blocks"]
