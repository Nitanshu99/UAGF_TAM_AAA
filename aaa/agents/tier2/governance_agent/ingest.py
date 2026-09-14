"""CGSA payload acquisition and validation for Phase 5."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.governance_agent.acquire import cgsa_source, pull_assessment
from aaa.agents.tier2.governance_agent.enrich import (
    domain_scores_for_chart,
    enrich_remediation_roadmap,
)
from aaa.agents.tier2.governance_agent.escalate import escalate_report
from aaa.agents.tier2.governance_agent.roadmap_rules import control_domains
from aaa.tools.cgsa_ingest import CGSAIngestError, IngestResult, cgsa_ingest
from aaa.tools.cgsa_pull import CGSAPullError


def acquire_and_validate(
    decl: dict[str, Any], engagement_id: str,
) -> Report | tuple[Any, IngestResult]:
    """Pull (or accept inline) the CGSA payload, validate, and enrich it.

    :param decl: Declaration summary from the dispatch.
    :param engagement_id: Engagement identifier.
    :returns: An escalation ``Report`` on failure, otherwise
        ``(payload, ingest_result)``.
    """
    payload = decl.get("cgsa_payload")
    source = cgsa_source(payload, decl.get("cgsa_assessment_id"), False)
    if payload is None:
        try:
            payload, source = pull_assessment(decl.get("cgsa_assessment_id") or "")
        except CGSAPullError as exc:
            return escalate_report(
                engagement_id, reason=f"cgsa_pull failed: {exc.reason}", details=exc.details)

    try:
        result = cgsa_ingest(payload, phase1_risk_tier=decl.get("risk_tier"), strict=False)
    except CGSAIngestError as exc:
        return escalate_report(
            engagement_id, reason=f"cgsa_ingest failed: {exc.reason}", details=exc.details)

    if result.schema_errors:
        return escalate_report(
            engagement_id,
            reason="cgsa_ingest schema validation failed",
            details={"errors": result.schema_errors[:5]},
        )

    source_remediation = (
        payload.get("remediation_roadmap", []) if isinstance(payload, dict) else [])
    result.state_delta["remediation_roadmap"] = enrich_remediation_roadmap(
        result.state_delta.get("remediation_roadmap", []),
        decl.get("organisation_contacts", {}) or {},
        source_remediation,
        control_domains(payload),
    )
    result.state_delta["cgsa_domain_scores"] = domain_scores_for_chart(payload)
    result.state_delta["cgsa_source"] = source
    return payload, result
