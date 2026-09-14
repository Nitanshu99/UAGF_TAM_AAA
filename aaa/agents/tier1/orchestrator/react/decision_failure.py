"""Recording a turn whose decide call failed, without letting it look like a move.

``DECISION_FAILED_ACTION`` is deliberately not one of the model's own actions:
``_dispatch_count``, ``_asked_for`` and the no-progress guard all read this history,
and a failed turn must not look to them like a move that was made.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.summary import _admitted, turn_outcome
from aaa.agents.tier1.orchestrator.react.turn import DECISION_FAILED_ACTION


def record_decision_failure(state: dict, history: list[dict[str, Any]],
                            turn: int, exc: BaseException) -> None:
    """Append this turn to the decision history as a failure.

    :param state: The AuditState dict, read for the turn outcome.
    :param history: Append-only decision/outcome log, extended in place.
    :param turn: The turn number.
    :param exc: What the decide call raised.
    """
    history.append({
        "turn": turn, "action": DECISION_FAILED_ACTION,
        "rationale": f"decide failed: {exc!r}"[:300],
        "outcome": turn_outcome(state, _admitted(state)),
    })


__all__ = ["record_decision_failure"]
