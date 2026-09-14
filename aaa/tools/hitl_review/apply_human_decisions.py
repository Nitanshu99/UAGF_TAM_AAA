"""Part 6 of the former ``hitl_review`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.hitl_review.build_hitl_review_packet import build_hitl_review_packet  # noqa: F401
from aaa.tools.hitl_review.case_entry import _case_entry  # noqa: F401
from aaa.tools.hitl_review.decision_to_verdict import (  # noqa: F401
    _apply_case,
    _decision_to_verdict,
)
from aaa.tools.hitl_review.decisions import apply_case_decisions
from aaa.tools.hitl_review.evidence_for_case import _evidence_for_case, hitl_cases  # noqa: F401
from aaa.tools.hitl_review.tid_phase import (  # noqa: F401
    _HITL_VERDICTS,
    _TID_PHASE,
    DECISION_ACCEPT,
    DECISION_OVERRIDE,
    DECISION_UPHOLD,
    _now,
)


def apply_human_decisions(state: dict, review: dict) -> dict[str, Any]:
    """Fold a human-edited review packet back into *state* (mutates + returns it).

    Returns a small summary dict: resolved/unresolved counts + per-case outcome.
    Does NOT recompute the compliance matrix — the caller runs
    ``node_compliance_matrix`` afterwards so verdicts/KPIs reflect the decisions.
    """
    critiques = state.setdefault("verifier_critiques", {})
    outcomes, resolved, unresolved = apply_case_decisions(review, critiques)
    # An artefact a human has now admitted is evidence again; release the articles
    # the Verifier's own verdict made insufficient, and nothing else (P6/Q1). Imported
    # here because the verification package imports this one at module load.
    from aaa.agents.tier1.phases.verification.unadmitted import (  # noqa: PLC0415
        clear_unadmitted_insufficiency,
    )

    released = clear_unadmitted_insufficiency(state)

    # Clear the HITL gate only when nothing remains escalated.
    still_escalated = any(
        c.get("verdict") in _HITL_VERDICTS for c in critiques.values()
    )
    state["hitl_required"] = still_escalated
    if not still_escalated:
        state["hitl_reason"] = None

    return {
        "resolved": resolved,
        "unresolved": unresolved,
        "still_hitl": still_escalated,
        "articles_released": released,
        "outcomes": outcomes,
    }
