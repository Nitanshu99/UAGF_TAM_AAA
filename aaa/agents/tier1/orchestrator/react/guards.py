"""Code-enforced hard gates around Orchestrator ReAct decisions.

The LLM drives the audit, but seven constraints are validated in code and a
non-compliant decision is *corrected* — never silently ignored — with the
override recorded in the decision history as an auditable event: the Art. 5
halt, the intake-completeness gate, the per-phase dispatch cap, (finding Q8) the
refusal to re-dispatch a phase that has already delivered, (finding F4) phase
precedence, the matrix-before-finalize ordering, and (finding F8) a repeat of an
action whose previous turn produced nothing. This is the "bounded autonomy"
contract from PROMPT.md §Agent 1 CRITICAL GATES.

On Q8: the audit had **two** mechanisms for one job. The phase's own loop
re-dispatches an agent whose artefact the Verifier rejected, carrying the
critique that ordered it and bounded by ``MAX_RERUNS``; the Orchestrator, seeing
the same rejection in its observation, re-dispatched the whole phase again — 907
seconds on top of 436, with no ``rerun_context`` and a second set of gate
entries. The division is now stated rather than emergent: **an artefact that
exists and was rejected is the phase loop's; a phase that has delivered nothing
is the Orchestrator's.**
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.close_gates import close_out_gates
from aaa.agents.tier1.orchestrator.react.coverage import PHASE_ARTEFACT
from aaa.agents.tier1.orchestrator.react.decisions import Decision
from aaa.agents.tier1.orchestrator.react.gate_checks import (
    _PHASE_CAP,
    INTAKE_GATE,
    _already_delivered,
    _dispatch_count,
    _intake_blocks,
)
from aaa.agents.tier1.orchestrator.react.prereqs import missing_prerequisite
from aaa.agents.tier1.orchestrator.react.repeat_guard import forward_move, no_progress_rewrite


def apply_guards(decision: Decision, state: dict[str, Any],
                 history: list[dict[str, Any]]) -> tuple[Decision, str | None]:
    """Validate *decision* against the hard gates.

    :param decision: The model's proposed decision.
    :type decision: Decision
    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :param history: Append-only decision/outcome log.
    :type history: list[dict[str, Any]]
    :returns: ``(possibly corrected decision, override note or None)``.
    :rtype: tuple[Decision, str | None]
    """
    if state.get("risk_tier") == "prohibited" and decision.action != "FINALIZE":
        return (Decision(action="FINALIZE", rationale="guard: Art. 5 halt"),
                "Art.5 prohibited practice — halted; only FINALIZE permitted")
    if decision.action == "DISPATCH" and _intake_blocks(decision.phase_id, state):
        return (Decision(action="FINALIZE", rationale="guard: intake gate"),
                f"intake_completeness_score {state.get('intake_completeness_score')} "
                f"< {INTAKE_GATE} blocks Phase 1")
    if (decision.action == "DISPATCH" and decision.phase_id
            and _dispatch_count(history, decision.phase_id) >= _PHASE_CAP):
        return (Decision(action="ASSEMBLE_MATRIX",
                         rationale="guard: dispatch cap"),
                f"phase {decision.phase_id} exceeded {_PHASE_CAP} dispatches")
    counts = {p: _dispatch_count(history, p) for p in PHASE_ARTEFACT}
    # Q8 / fix 32: re-running a phase whose artefact was rejected belongs to the
    # phase's own loop, which holds the critique, the rerun_context and the
    # budget. The Orchestrator dispatches a phase that has delivered nothing.
    if (decision.action == "DISPATCH" and decision.phase_id
            and _already_delivered(decision.phase_id, state, history)):
        forward = forward_move(state, counts, _PHASE_CAP, "re-dispatch is the phase's")
        target = f"{forward.action} {forward.phase_id}" if forward.phase_id else forward.action
        return forward, (
            f"{decision.phase_id} has already delivered its artefact — a rejected "
            f"artefact is re-run by the phase's own verification loop, with the "
            f"critique that ordered it; redirected to {target}")
    if decision.action == "DISPATCH" and decision.phase_id:
        # F4: turn 1 dispatched P2 while P1 had never run, on the strength of
        # three intake artefacts whose ids start T01.
        owed = missing_prerequisite(decision.phase_id, state, history,
                                    counts, _PHASE_CAP)
        if owed and not _intake_blocks(owed, state):
            return (Decision(action="DISPATCH", phase_id=owed,
                             rationale="guard: phase precedence"),
                    f"{decision.phase_id} depends on {owed}, which has produced no "
                    f"artefact — dispatching {owed} first")
    closing = close_out_gates(decision, state, counts, _PHASE_CAP)
    if closing is not None:
        return closing
    return no_progress_rewrite(decision, state, history, counts, _PHASE_CAP)
