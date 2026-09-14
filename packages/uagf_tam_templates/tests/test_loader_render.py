"""Smoke tests for the Jinja partial environment and rendering."""
from __future__ import annotations

import uagf_tam_templates as utt


def test_partial_env_finds_packaged_t17_partial():
    env = utt.partial_env()
    assert env.get_template("T17_compliance_matrix.j2") is not None


def test_render_partial_t17_outputs_markdown_table():
    md = utt.render_partial("T17_compliance_matrix", {
        "engagement_id": "eng-x",
        "risk_tier": "high",
        "in_scope_articles": ["Art.9", "Art.43"],
        "final_verdict": "PASS",
        "articles": [
            {"article": "Art.9", "verdict": "PASS", "evidence_uris": ["minio://x/T14"]},
            {"article": "Art.43", "verdict": "PASS", "evidence_uris": ["minio://x/T05"]},
        ],
        "kpi_summary": {
            "intake_completeness_score": 1.0,
            "completeness_score": 0.9,
            "regulatory_coverage_pct": 100.0,
        },
        "generated_at": "2025-01-01T00:00:00Z",
    })
    assert "# Compliance Matrix — eng-x" in md
    assert "| Art.9 | PASS |" in md
    assert "minio://x/T05" in md


def test_render_partial_t18_outputs_kpi_summary():
    md = utt.render_partial("T18_audit_report", {
        "engagement_id": "eng-y",
        "final_verdict": "PASS_WITH_OBSERVATIONS",
        "risk_tier": "high",
        "modality": "tabular",
        "intake_completeness_score": 1.0,
        "completeness_score": 0.88,
        "regulatory_coverage_pct": 88.9,
        "blocking_findings": [],
        "positive_findings": [{"id": "pf-1", "title": "All in order"}],
    })
    assert "Audit Report — eng-y" in md
    assert "PASS_WITH_OBSERVATIONS" in md
    assert "88.9" in md
