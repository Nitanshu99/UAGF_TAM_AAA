"""Part 3 of the former ``node_stubs`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.node_stubs.logger import (  # noqa: F401
    TEMPLATE_ARTICLES,
    _mark_stub_insufficient,
    _stub_artefact,
    _stub_critique,
    logger,
    node_phase1_stub,
)
from aaa.agents.tier1.phases.nodes.route import (  # noqa: F401
    node_parallel_phases_stub,
    node_phase5_stub,
    node_route,
)
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION, FAIL


def node_hitl_checkpoint(state: dict) -> dict:
    """HITL checkpoint — flags engagements that need human review.

    The pipeline no longer halts here; HITL cases continue to Phase 6, which
    emits a provisional report plus a review packet resolved later via
    ``scripts/finalize_hitl.py``.
    """
    # A disclaimer means the audit could not conclude — the case most in need
    # of a human, and previously the only adverse outcome that slipped past.
    needs_hitl = (state.get("hitl_required")
                  or state.get("final_verdict") in {FAIL, DISCLAIMER_OF_OPINION})
    if needs_hitl:
        reason = (state.get("hitl_reason")
                  or "FAIL / disclaimer verdict or manual escalation")
        logger.warning("HITL required (%s) — provisional report will be emitted.", reason)
    return state


def node_phase6_stub(state: dict) -> dict:
    """Phase 6 stub — used when ReportArchitect is not wired."""
    logger.info("Engagement %s: Phase 6 (Report) — stub", state["engagement_id"])
    for tid in ["T17_compliance_matrix", "T18_audit_report"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
    return state


__all__ = [
    "node_phase1_stub",
    "node_route",
    "node_parallel_phases_stub",
    "node_phase5_stub",
    "node_hitl_checkpoint",
    "node_phase6_stub",
]
