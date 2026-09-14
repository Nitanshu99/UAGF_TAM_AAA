"""Finding F8 — stop an action that changed nothing from being taken again.

The assessed run spent 22 of its 24 turns (~570 s, ~119,000 tokens) re-emitting
an identical no-op ``PLAN``, and nothing noticed: ``apply_guards`` reasoned about
Art. 5, the intake gate, the dispatch cap and close-out ordering, but never about
whether the *previous* turn had accomplished anything. ``MAX_TURNS`` was the only
bound, and reaching it silently cancelled six mandatory phases (F12).

Adding ``ESCALATE_HITL`` to the vocabulary would have moved that livelock rather
than ended it, so the two changes belong together: an escalation already on
record must not be recordable a second time either.

The rewrite is a strictly-progressing ladder — outstanding mandatory work, then
matrix assembly, then close-out — and never rewrites a decision to itself.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.assembled import matrix_assembled
from aaa.agents.tier1.orchestrator.react.coverage import pending_mandatory
from aaa.agents.tier1.orchestrator.react.decisions import Decision


def _asked_for(entry: dict[str, Any]) -> tuple[Any, Any]:
    """The move the model asked for on that turn, not the one a guard substituted.

    Comparing executed actions only would let the model alternate — propose the
    no-op, get redirected, propose it again — and the redirect's own progress
    would mask the repetition.

    :param entry: One decision-history entry.
    :returns: ``(action, phase_id)`` as proposed.
    """
    if entry.get("proposed_action"):
        return entry["proposed_action"], entry.get("proposed_phase_id")
    return entry.get("action"), entry.get("phase_id")


def _repeats(decision: Decision, last: tuple[Any, Any]) -> bool:
    """Is *decision* the same move as *last*?

    :param decision: The model's proposed decision.
    :param last: ``(action, phase_id)`` from the previous turn.
    :returns: ``True`` when the action (and, for a dispatch, the phase) match.
    """
    action, phase_id = last
    if action != decision.action:
        return False
    return decision.action != "DISPATCH" or phase_id == decision.phase_id


def forward_move(state: dict[str, Any], dispatched: dict[str, int],
                 cap: int, reason: str) -> Decision:
    """The next strictly-progressing move: outstanding work, then matrix, then close.

    One ladder, asked by every guard that has to redirect a decision somewhere —
    the no-progress rewrite and (fix 32) the re-dispatch refusal.

    :param state: The AuditState dict.
    :param dispatched: Dispatch counts per phase id so far.
    :param cap: Maximum dispatches allowed per phase.
    :param reason: Short guard name recorded in the decision's rationale.
    :returns: The decision to take instead.
    """
    owed = pending_mandatory(state, dispatched, cap)
    if owed:
        return Decision(action="DISPATCH", phase_id=owed, rationale=f"guard: {reason}")
    if not matrix_assembled(state):
        return Decision(action="ASSEMBLE_MATRIX", rationale=f"guard: {reason}")
    return Decision(action="FINALIZE", rationale=f"guard: {reason}")


def no_progress_rewrite(decision: Decision, state: dict[str, Any],
                        history: list[dict[str, Any]],
                        dispatched: dict[str, int],
                        cap: int) -> tuple[Decision, str | None]:
    """Redirect a repeat of a move that the previous turn showed leads nowhere.

    "Leads nowhere" is either: the turn admitted no artefact, or the same move
    was already overridden by this guard and the model is asking again.

    :param decision: The model's proposed decision.
    :param state: The mutable AuditState dict.
    :param history: Append-only decision/outcome log.
    :param dispatched: Dispatch counts per phase id so far.
    :param cap: Maximum dispatches allowed per phase.
    :returns: ``(possibly corrected decision, override note or None)``.
    """
    if not history:
        return decision, None
    last = history[-1]
    stalled = (not (last.get("outcome") or {}).get("new_artefacts")
               or bool(last.get("proposed_action")))
    if not _repeats(decision, _asked_for(last)) or not stalled:
        return decision, None

    forward = forward_move(state, dispatched, cap, "no-progress repeat")
    if _repeats(forward, (decision.action, decision.phase_id)):
        return decision, None  # nothing further forward exists — let the budget bound it
    target = f"{forward.action} {forward.phase_id}" if forward.phase_id else forward.action
    return forward, (
        f"{decision.action} repeats the previous turn, which made no "
        f"progress — redirected to {target}")


__all__ = ["forward_move", "no_progress_rewrite"]
