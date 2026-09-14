"""Smoke tests for schema validation of template instances."""
from __future__ import annotations

import pytest
import uagf_tam_templates as utt


def test_validate_accepts_minimal_t17_instance():
    instance = {
        "engagement_id": "eng-x",
        "risk_tier": "high",
        "is_llm_or_agentic": False,
        "in_scope_articles": ["Art.9"],
        "articles": [{
            "article": "Art.9", "verdict": "PASS",
            "evidence_uris": ["minio://x/T14"],
            "supporting_template_ids": ["T14_governance_findings"],
            "source_phase": "P5",
        }],
        "kpi_summary": {
            "intake_completeness_score": 1.0,
            "completeness_score": 0.9,
            "regulatory_coverage_pct": 100.0,
        },
        "final_verdict": "PASS",
        "generated_at": "2025-01-01T00:00:00Z",
    }
    # This is the smoke contract: a valid instance must not be rejected.
    try:
        utt.validate("T17_compliance_matrix", instance)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"valid T17 instance was rejected: {exc}")


def test_validate_rejects_missing_required_field():
    import jsonschema
    with pytest.raises(jsonschema.ValidationError):
        utt.validate("T17_compliance_matrix", {"engagement_id": "eng-y"})
