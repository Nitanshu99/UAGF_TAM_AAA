"""The gates that decide whether the audit may close: mandatory phases, then the matrix.

The loop executes ``DISPATCH P6`` by running the report and stopping, so it *is* the
close-out and both gates here have to recognise it as one.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.assembled import matrix_assembled
from aaa.agents.tier1.orchestrator.react.coverage import pending_mandatory
from aaa.agents.tier1.orchestrator.react.decisions import Decision


def close_out_gates(decision: Decision, state: dict[str, Any],
                    counts: dict[str, int], phase_cap: int
                    ) -> tuple[Decision, str] | None:
    """Refuse a close-out that would overstate conformity.

    :param decision: The decision as the earlier gates left it.
    :param state: The AuditState dict.
    :param counts: Dispatches so far, per phase.
    :param phase_cap: Dispatches allowed per phase.
    :returns: ``(corrected decision, note)``, or ``None`` when nothing blocks it.
    """
    # The loop executes `DISPATCH P6` by running the report and stopping, so it
    # *is* the close-out and the two gates below must recognise it as one.
    finalizing = (decision.action == "FINALIZE"
                  or (decision.action == "DISPATCH" and decision.phase_id == "P6"))
    if finalizing or decision.action == "ASSEMBLE_MATRIX":
        owed = pending_mandatory(state, counts, phase_cap)
        if owed:
            return (Decision(action="DISPATCH", phase_id=owed,
                             rationale="guard: mandatory phase not yet run"),
                    f"mandatory phase {owed} has produced no artefact — "
                    "closing the audit now would overstate conformity")
    if finalizing and not matrix_assembled(state):
        return (Decision(action="ASSEMBLE_MATRIX",
                         rationale="guard: matrix before finalize"),
                "FINALIZE requires an assembled compliance matrix")
    return None


__all__ = ["close_out_gates"]
