"""Part 5 of the former ``hitl_review`` module (auto-split)."""
from __future__ import annotations

from aaa.tools.hitl_review.build_hitl_review_packet import build_hitl_review_packet  # noqa: F401
from aaa.tools.hitl_review.case_entry import _case_entry  # noqa: F401
from aaa.tools.hitl_review.evidence_for_case import _evidence_for_case, hitl_cases  # noqa: F401
from aaa.tools.hitl_review.tid_phase import (  # noqa: F401
    _HITL_VERDICTS,
    _TID_PHASE,
    DECISION_ACCEPT,
    DECISION_OVERRIDE,
    DECISION_UPHOLD,
    _now,
)


def _decision_to_verdict(decision: str, suggested: str) -> str | None:
    """Map a human decision to the Verifier verdict to record, or None to keep."""
    decision = (decision or "").strip().lower()
    if decision == DECISION_ACCEPT:
        return "accept_with_notes"  # human-admitted (notes: human review)
    if decision == DECISION_OVERRIDE:
        sv = (suggested or "").strip()
        return sv or None
    if decision == DECISION_UPHOLD:
        return "escalate_hitl"  # unchanged; remains a blocking concern
    return None  # blank / unrecognised → leave the case unresolved


def _apply_case(crit: dict, case: dict) -> bool:
    """Apply one human decision to its critique; True when resolved.

    :param crit: The Verifier critique (mutated in place when resolved).
    :param case: The human-edited review case.
    """
    new_verdict = _decision_to_verdict(
        case.get("human_decision", ""), case.get("human_suggested_verdict", ""))
    if new_verdict is None or new_verdict == "escalate_hitl":
        return False
    crit["verdict"] = new_verdict
    crit["rerun_required"] = new_verdict == "rerun"
    note = (
        f"HITL resolved by {case.get('reviewed_by') or 'human reviewer'}: "
        f"{case.get('human_decision')}. {case.get('human_rationale') or ''}"
    ).strip()
    crit.setdefault("notes", []).append(note)
    crit["human_reviewed"] = True
    return True
