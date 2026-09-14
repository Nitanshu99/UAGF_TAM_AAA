"""Folding each human decision in a review packet onto the artefact's critique."""
from __future__ import annotations

from typing import Any

from aaa.tools.hitl_review.decision_to_verdict import _apply_case


def apply_case_decisions(review: dict, critiques: dict) -> tuple[list, int, int]:
    """Apply each case's human decision to the critique it names.

    :param review: The human-edited review packet.
    :param critiques: ``verifier_critiques`` from the state, mutated in place.
    :returns: ``(outcomes, resolved, unresolved)``.
    """
    outcomes: list[dict[str, Any]] = []
    resolved = unresolved = 0
    for case in review.get("cases", []) or []:
        tid = case.get("template_id")
        if not tid or tid not in critiques:
            continue
        if _apply_case(critiques[tid], case):
            resolved += 1
            outcome = "resolved"
        else:
            unresolved += 1
            outcome = "unresolved"
        outcomes.append({"template_id": tid, "outcome": outcome,
                         "verdict": critiques[tid].get("verdict")})
    return outcomes, resolved, unresolved


__all__ = ["apply_case_decisions"]
