"""Finding F2 — carry the Verifier's critique into the rerun that it ordered.

``run_phase_with_verification`` used to re-dispatch an unmutated ``Dispatch``,
so a rerun re-sent a byte-identical prompt: the agent was asked the same
question again and told nothing about why its answer had been rejected.  The
architecture's central quality mechanism — verify, then re-run with feedback —
degenerated to re-sampling the same prompt and hoping for a better draw.

The ``Dispatch`` contract already documented a ``rerun_context`` field ("or
Critique object if this is a rerun"); nothing ever populated it.  This module
builds what goes in it.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.verifier.issues import is_defect

#: Verdicts meaning the artefact was not admitted and must be reworked.
_FAILING = ("rerun", "escalate_hitl")


def rerun_requested(state: dict, tids: list[str]) -> list[str]:
    """Template ids the Verifier sent back for another attempt.

    Asked per artefact rather than of the phase's worst verdict, which is fix
    32's whole point.  ``escalate_hitl`` outranks ``rerun`` in ``_VERDICT_ORDER``,
    so a phase where one artefact escalated and another was sent back closed on
    ``escalate_hitl`` and **never reran** — the rerun the Verifier ordered was
    silently dropped because a sibling had a worse problem.  On case 01 that was
    T11: *"received a 'rerun' verdict with 0 reruns used"*, which the Orchestrator
    then noticed and papered over by re-dispatching the whole phase itself (Q8).

    The two verdicts are not alternatives. An escalated artefact needs a human;
    an artefact sent back needs another attempt; re-dispatching the phase serves
    the second without costing the first, because the rerun re-critiques both.

    :param state: The AuditState, holding ``verifier_critiques``.
    :param tids: Template ids this phase produced.
    :returns: The tids whose current verdict is ``rerun``.
    """
    critiques = state.get("verifier_critiques") or {}
    return [tid for tid in tids
            if (critiques.get(tid) or {}).get("verdict") == "rerun"]


def build_rerun_context(state: dict, tids: list[str], attempt: int) -> dict[str, Any]:
    """Summarise the critiques that forced a rerun, for the agent's next attempt.

    :param state: The mutable AuditState, holding ``verifier_critiques``.
    :param tids: Template ids this phase produced.
    :param attempt: 1-based number of the rerun about to be dispatched.
    :returns: A ``rerun_context`` payload naming each rejected artefact and the
        issues raised against it.
    """
    critiques = state.get("verifier_critiques") or {}
    rejected: list[dict[str, Any]] = []
    for tid in tids:
        crit = critiques.get(tid) or {}
        if crit.get("verdict") not in _FAILING:
            continue
        rejected.append({
            "template_id": tid,
            "verdict": crit.get("verdict"),
            # Only what a rerun can fix: findings about the provider go to the matrix.
            "issues": [i for i in crit.get("issues") or [] if is_defect(i)],
            "notes": crit.get("notes") or [],
            "scores": crit.get("scores") or {},
        })
    return {
        "reason": "verifier_rerun",
        "attempt": attempt,
        "rejected_artefacts": rejected,
    }


__all__ = ["build_rerun_context", "rerun_requested"]
