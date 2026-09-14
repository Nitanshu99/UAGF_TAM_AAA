"""Part 2 of the former ``initial_state`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.initial_state.empty_cgsa_state import _empty_cgsa_state  # noqa: F401


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
        "annex_i_section_a_acts": list(stage_a.get("annex_i_section_a", []) or []),
        "harmonised_standards_applied": False,
        "annex_iii_mapping": [],
        "declaration_verification": {},
        "art43_decision": None,
        "phase_status": {},
        "phase_artefacts": {},
        **_empty_cgsa_state(),
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
        "hitl_alerts": [],
        "latest_report": None,
        "latest_critique": None,
        "low_confidence_phases": [],
        "unadmitted_artefacts": [],
    }


__all__ = ["build_initial_state"]
