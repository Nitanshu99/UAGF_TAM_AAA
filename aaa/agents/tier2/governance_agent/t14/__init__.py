"""T14 Governance Findings artefact builder (§5.4 hand-off surface)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.t14.details import (
    domains_section,
    hard_constraints_section,
    low_confidence_section,
)
from aaa.agents.tier2.governance_agent.t14.remediation import remediation_section
from aaa.agents.tier2.governance_agent.t14.sections import (
    blocking_findings_section,
    metadata_section,
    positive_findings_section,
    scores_section,
)
from aaa.agents.tier2.governance_agent.t14.tail import tail_sections
from aaa.tools.cgsa_ingest import IngestResult


def build_t14(
    engagement_id: str,
    result: IngestResult,
    decl: dict[str, Any],
    spawn: dict[str, Any],
    risk_tier_mismatch: bool,
    now: str,
) -> dict[str, Any]:
    """Build the T14 Governance Findings payload.

    :param engagement_id: Engagement identifier.
    :param result: Validated CGSA ingest result.
    :param decl: Declaration summary from the dispatch.
    :param spawn: Tier-3 spawn decisions.
    :param risk_tier_mismatch: Phase 1 vs CGSA risk-tier disagreement.
    :param now: ISO-8601 generation timestamp.
    :returns: T14 payload matching the template schema.
    """
    payload = result.payload
    metadata = payload.get("metadata", {}) or {}
    handoff = payload.get("aaa_phase5_handoff", {}) or {}
    return {
        "engagement_id": engagement_id,
        "cgsa_schema_version": result.schema_version,
        "cgsa_metadata": metadata_section(metadata),
        "overall_scores": scores_section(payload.get("overall_scores", {}) or {}),
        "phase5_verdict": result.state_delta.get("cgsa_phase5_verdict")
            or handoff.get("phase5_verdict") or "PASS_WITH_OBSERVATIONS",
        "phase5_narrative_summary": handoff.get("phase5_narrative_summary", ""),
        "blocking_findings_count": int(handoff.get("blocking_findings_count", 0) or 0),
        "blocking_findings": blocking_findings_section(handoff),
        "positive_findings": positive_findings_section(handoff),
        "low_confidence_controls": low_confidence_section(result),
        "domains": domains_section(payload),
        "hard_constraint_results": hard_constraints_section(
            payload.get("hard_constraint_results", {}) or {}),
        "remediation_roadmap": remediation_section(result),
        **tail_sections(result, decl, spawn, risk_tier_mismatch, metadata, handoff),
        "generated_at": now,
    }
