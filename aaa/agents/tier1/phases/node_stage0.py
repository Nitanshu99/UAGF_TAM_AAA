"""
aaa.agents.tier1.phases.node_stage0 — Intake validation gate node.

Single exported function: ``node_stage0(state)``.

Checks intake_completeness_score >= 0.80 before advancing to Phase 1.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def node_stage0(state: dict) -> dict:
    """Stage 0 — intake completeness gate.

    Blocks the engagement with a HITL flag if the completeness score
    is below the 0.80 threshold mandated by §9.1.
    """
    score = state.get("intake_completeness_score") or 0.0
    if score < 0.80:
        state["hitl_required"] = True
        state["hitl_reason"] = (
            f"intake_completeness_score={score:.2f} is below the 0.80 gate. "
            "Client must remediate missing Annex IV fields before Phase 1 can run."
        )
        logger.warning(
            "Engagement %s blocked at Stage 0: score=%.2f",
            state["engagement_id"],
            score,
        )
    return state


__all__ = ["node_stage0"]
