"""An assembled matrix with no rows still lets the audit close (T-20260913-087).

Case 02 verified minimal-risk: no article binds it, the matrix is {}, and the
close-out gate re-assembled it every turn instead of finalising.
"""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.react.close_gates import close_out_gates
from aaa.agents.tier1.orchestrator.react.decisions import Decision


def _state(**over):
    return {"phase_plan": {}, "phase_artefacts": {}, "compliance_matrix": {}, **over}


def test_an_empty_assembled_matrix_finalises() -> None:
    state = _state(final_verdict="DISCLAIMER_OF_OPINION")
    assert close_out_gates(Decision(action="FINALIZE", rationale="done"), state, {}, 2) is None


def test_an_unassembled_matrix_is_still_assembled_first() -> None:
    corrected = close_out_gates(Decision(action="FINALIZE", rationale="done"), _state(final_verdict=None), {}, 2)
    assert corrected is not None and corrected[0].action == "ASSEMBLE_MATRIX"
