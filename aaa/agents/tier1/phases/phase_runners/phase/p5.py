"""Part 6 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris
from aaa.agents.tier1.phases.node_stubs import node_phase5_stub
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p3 import run_phase_3  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p4 import run_phase_4  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification
from aaa.platform.state.contacts import declared_contacts
from aaa.tools.regulatory_coverage.binding import binding_articles


async def run_phase_5(agent: Any, state: dict) -> dict:
    """Run GovernanceAgent (Phase 5)."""
    if agent is None:
        return node_phase5_stub(state)
    eng = state["engagement_id"]
    stage_a = state.get("client_submission", {}).get("stage_a", {}) or {}
    dispatch = Dispatch(
        phase_id="P5",
        task_brief="Pull S4 CGSA payload, cross-check risk_tier, produce T14 + T15.",
        evidence_uris=_evidence_uris(state),
        output_contract="T14_governance_findings",
        declaration_summary={
            "engagement_id": eng,
            # M13: without this key `gather_context` skips client-document
            # retrieval entirely, and Phase 5 ran the 2026-09-10 Mariposa
            # engagement on `client_doc_hits: 0` — missing the provider's
            # Art. 9 risk-management file T14 is accountable for, which Phase 1
            # retrieved from the same collection in the same run.
            "client_doc_collection": state.get("client_doc_collection"),
            "risk_tier": state.get("risk_tier", ""),
            # The list the Verifier judges T14/T15 against, so Phase 5 cannot call a
            # gate-scoped article unbound (T-20260914-055).
            "binding_articles": binding_articles(state),
            "cgsa_assessment_id": stage_a.get("cgsa_assessment_id"),
            "cgsa_payload": state.get("cgsa_payload"),
            "gdpr_overlap": stage_a.get("gdpr_overlap", False),
            "special_category_data": stage_a.get("special_category_data", False),
            # Read by `acquire_and_validate` to name remediation owners; nothing
            # passed it, so every roadmap owner was unassigned (T-20260913-042).
            "organisation_contacts": declared_contacts(stage_a.get("organisation_contacts")),
        },
    )
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            # Art. 14 (human oversight) joins its accountable artefact — CGSA
            # domain D5 arrives inside T14 (fix 31, Q1).
            "T14_governance_findings": ["Art.9", "Art.14", "Art.17"],
            "T15_monitoring_logging_review": ["Art.12", "Art.72"],
        },
        phase_label="Phase 5 GovernanceAgent", default_confidence=0.85,
    )
    if report is None:
    # Fix 35: the *unwired* path above still stubs — no dispatch was attempted
    # and a deterministic placeholder is an honest answer there. A phase that
    # was dispatched and failed is a different fact, and `gate_on_no_report`
    # has already recorded it: no artefact, articles held, a finding naming
    # the cause. Writing a stub here instead is what produced R2 and R3.
        return state
    logger.info("Engagement %s: Phase 5 complete.", eng)
    return state
