"""
aaa.agents.tier1.phases.initial_state — Seed AuditState for a new engagement.

Single exported function: ``build_initial_state(engagement_id, client_submission)``.
"""
from __future__ import annotations

from typing import Any


def build_initial_state(engagement_id: str, client_submission: dict[str, Any]) -> dict[str, Any]:
    """Return a fully-initialised AuditState dict for a new engagement.

    Parameters
    ----------
    engagement_id:
        The unique engagement identifier.
    client_submission:
        The raw intake payload (stage_a, stage_b, optional stage_c).
    """
    stage_a = client_submission.get("stage_a", {})
    return {
        "engagement_id": engagement_id,
        "client_doc_collection": client_submission.get("client_doc_collection"),
        "client_submission": client_submission,
        "declared_modality": stage_a.get("declared_modality", "tabular"),
        "declared_risk_tier": stage_a.get("declared_risk_tier", "minimal"),
        "declared_annex_iii_sections": stage_a.get("declared_annex_iii_sections", []),
        "risk_tier": stage_a.get("declared_risk_tier", "minimal"),
        "modality": stage_a.get("declared_modality", "tabular"),
        "deployment_context": stage_a.get("deployment_context", "b2b"),
        "is_llm_or_agentic": stage_a.get("declared_modality", "") in {
            "llm", "agentic", "gpai"
        },
        "provider_elects_third_party": stage_a.get("provider_elects_third_party", False),
        "harmonised_standards_applied": False,
        "annex_iii_mapping": [],
        "declaration_verification": {},
        "art43_decision": None,
        "phase_status": {},
        "phase_artefacts": {},
        "cgsa_payload": None,
        "cgsa_schema_version": None,
        "cgsa_composite_maturity_score": None,
        "cgsa_composite_maturity_label": None,
        "cgsa_domain_scores": None,
        "cgsa_eu_ai_act_coverage_pct": None,
        "cgsa_csp_satisfiable": None,
        "cgsa_governance_verdict": None,
        "cgsa_phase5_verdict": None,
        "cgsa_phase5_narrative": None,
        "cgsa_blocking_findings": [],
        "cgsa_positive_findings": [],
        "cgsa_low_confidence_controls": [],
        "cgsa_recommended_follow_up": [],
        "cgsa_report_url": None,
        "cgsa_risk_tier_match": None,
        "compliance_matrix": {},
        "blocking_findings": [],
        "positive_findings": [],
        "remediation_roadmap": [],
        "material_findings_count": None,
        "possibly_material_findings_count": None,
        "verifier_critiques": {},
        "intake_completeness_score": client_submission.get("intake_completeness_score"),
        "completeness_score": None,
        "regulatory_coverage_pct": None,
        "final_verdict": None,
        "auditor_opinion": None,
        "hitl_required": False,
        "hitl_reason": None,
    }


__all__ = ["build_initial_state"]
