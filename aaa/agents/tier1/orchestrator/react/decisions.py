"""Typed decision contract for the Orchestrator ReAct protocol.

Mirrors PROMPT.md §Agent 1: every Orchestrator reply is a single JSON object
whose ``action`` is one of ``PLAN | DISPATCH | ESCALATE_HITL |
ASSEMBLE_MATRIX | FINALIZE``; a ``DISPATCH`` additionally names the phase to
run. Reply-shape tolerance lives in :mod:`.shapes`; anything still unrecognised
raises :class:`DecisionError` so the loop can fall back deterministically rather
than act on a malformed instruction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aaa.agents.tier1.orchestrator.react.shapes import (  # noqa: F401
    action_of,
    normalise_phase,
    unwrap,
)

#: ``ESCALATE_HITL`` exists because the prompt has always ordered the model to
#: "emit a HITL alert" and the vocabulary had no token for it (finding F8): the
#: model narrated "Audit remains paused" through 22 no-op ``PLAN``s because that
#: was the least-wrong legal move. It records an alert and the audit *continues*
#: — the runtime has not halted on HITL since the provisional-report rework.
ACTIONS: tuple[str, ...] = ("PLAN", "DISPATCH", "ESCALATE_HITL",
                            "ASSEMBLE_MATRIX", "FINALIZE")

#: phase ids the LLM may dispatch, mapped by the loop onto phase runners.
DISPATCHABLE_PHASES: tuple[str, ...] = (
    "P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIVACY")


class DecisionError(ValueError):
    """Raised when the model reply is not a valid ReAct decision."""


@dataclass(frozen=True)
class Decision:
    """One validated Orchestrator decision.

    :param action: One of :data:`ACTIONS`.
    :param phase_id: Target phase for ``DISPATCH`` (else ``None``).
    :param task_brief: Optional natural-language brief for the phase agent.
    :param rationale: Model-supplied one-line rationale (audit trail).
    :param raw: The full parsed reply, kept for the audit log.
    """

    action: str
    phase_id: str | None = None
    task_brief: str = ""
    rationale: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def parse_decision(payload: Any) -> Decision:
    """Validate *payload* into a :class:`Decision`.

    :param payload: Parsed JSON reply from the Orchestrator model.
    :type payload: Any
    :returns: The validated decision.
    :rtype: Decision
    :raises DecisionError: On a non-dict payload, unknown action, or a
        ``DISPATCH`` without a recognised ``phase_id``.
    """
    payload = unwrap(payload)
    if not isinstance(payload, dict):
        raise DecisionError(f"decision payload must be an object, got {type(payload).__name__}")
    action = action_of(payload)
    if action not in ACTIONS:
        raise DecisionError(f"unknown action: {action!r}")
    phase_id = payload.get("phase_id")
    if action == "DISPATCH":
        phase_id = normalise_phase(phase_id)
        if phase_id not in DISPATCHABLE_PHASES:
            raise DecisionError(f"DISPATCH requires a known phase_id, got {phase_id!r}")
    else:
        phase_id = None
    return Decision(action=action, phase_id=phase_id,
                    task_brief=str(payload.get("task_brief") or ""),
                    rationale=str(payload.get("rationale") or ""), raw=payload)
