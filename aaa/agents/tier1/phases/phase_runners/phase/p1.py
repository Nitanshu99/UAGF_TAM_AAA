"""Part 2 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris
from aaa.agents.tier1.phases.node_stubs import node_phase1_stub
from aaa.agents.tier1.phases.nodes.verified_tier import apply_verified_tier
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification


async def run_phase_1(agent: Any, state: dict) -> dict:
    """Run ScopeAgent (Phase 1); fall back to stub on error."""
    if agent is None:
        return node_phase1_stub(state)
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="P1",
        task_brief="Verify declared modality, risk tier, and Annex III sections.",
        evidence_uris=_evidence_uris(state),
        output_contract="T02_system_card",
        declaration_summary={
            "engagement_id": eng,
            "client_doc_collection": state.get("client_doc_collection"),
            "declared_modality": state.get("declared_modality", ""),
            "declared_risk_tier": state.get("declared_risk_tier", ""),
            "declared_annex_iii_sections": state.get("declared_annex_iii_sections", []),
            "deployment_context": state.get("deployment_context", ""),
            # Set by Phase 5; on a re-entry Art. 43 must see it (T-20260913-016).
            "harmonised_standards_applied": bool(state.get("harmonised_standards_applied")),
        },
    )
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            "T02_system_card": ["Art.5", "Art.13"],
            "T03_annex_iii_mapping": ["Art.6", "Annex_III"],
            "T04_risk_tier_decision": ["Art.5", "Art.6"],
            "T05_art43_decision": ["Art.43"],
        },
        phase_label="Phase 1 ScopeAgent", default_confidence=0.9,
    )
    if report is None:
    # Fix 35: the *unwired* path above still stubs — no dispatch was attempted
    # and a deterministic placeholder is an honest answer there. A phase that
    # was dispatched and failed is a different fact, and `gate_on_no_report`
    # has already recorded it: no artefact, articles held, a finding naming
    # the cause. Writing a stub here instead is what produced R2 and R3.
        return state
    logger.info("Engagement %s: Phase 1 complete.", eng)
    return apply_verified_tier(state)
