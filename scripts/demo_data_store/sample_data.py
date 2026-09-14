"""Sample payloads used by the data-store demo."""
from __future__ import annotations

from typing import Any

ENGAGEMENT_ID = "demo-eng-001"

STAGE_A: dict[str, Any] = {
    "declared_modality": "tabular",
    "declared_risk_tier": "high",
    "intended_purpose": "credit scoring",
    "deployment_context": "b2b",
    "provider_name": "Acme Corp",
}

STAGE_B: dict[str, Any] = {"general_description": "XGBoost credit risk model"}

AUDIT_RESULT: dict[str, Any] = {
    "final_verdict": "PASS_WITH_OBSERVATIONS",
    "intake_completeness_score": 0.88,
    "completeness_score": 0.91,
    "regulatory_coverage_pct": 87.5,
    "material_findings_count": 0,
    "possibly_material_findings_count": 2,
    "auditor_opinion": "System demonstrates reasonable compliance with EU AI Act.",
    "art43_decision": {"procedure": "internal_control",
                       "rationale": "No Annex III sec 1."},
    "blocking_findings": [],
    "positive_findings": [{"id": "pf1", "title": "Data governance documented"}],
    "remediation_roadmap": [{"action": "Add post-market monitoring plan"}],
    "compliance_matrix": {"Art.5": "PASS", "Art.10": "PASS", "Art.13": "PASS"},
    "phase_artefacts": {"T02_system_card": {"uri": "minio://demo-eng-001/T02"}},
}
