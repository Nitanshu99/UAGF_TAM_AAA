"""Smoke tests for the uagf-tam-templates loader API (≥80 % coverage gate)."""
from __future__ import annotations

import json
import pathlib

import pytest

import uagf_tam_templates as utt


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def test_list_templates_contains_t01a_to_t18():
    ids = utt.list_templates()
    # ARCHITECTURE §4A guarantees T01a + T01b + T01c + T02..T16 + T17 + T18.
    expected_prefixes = (
        "T01a_stage_a_triage",
        "T01b_annex_iv_dossier",
        "T01c_intake_completeness_report",
        "T02_system_card",
        "T17_compliance_matrix",
        "T18_audit_report",
    )
    for prefix in expected_prefixes:
        assert prefix in ids, f"missing template: {prefix}"
    assert len(ids) >= 18


def test_schema_path_returns_existing_file():
    p = utt.schema_path("T17_compliance_matrix")
    assert isinstance(p, pathlib.Path) and p.is_file()


def test_schema_path_raises_for_unknown_template():
    with pytest.raises(utt.SchemaNotFoundError):
        utt.schema_path("T99_does_not_exist")


# ---------------------------------------------------------------------------
# Schema loading & validation
# ---------------------------------------------------------------------------

def test_load_schema_returns_jsonschema_draft7():
    schema = utt.load_schema("T17_compliance_matrix")
    assert schema["$schema"].endswith("draft-07/schema#")
    assert "properties" in schema and "required" in schema


def test_load_schema_is_cached():
    a = utt.load_schema("T17_compliance_matrix")
    b = utt.load_schema("T17_compliance_matrix")
    assert a is b  # lru_cache hit


def test_validate_accepts_minimal_t17_instance():
    instance = {
        "engagement_id": "eng-x",
        "risk_tier": "high",
        "is_llm_or_agentic": False,
        "in_scope_articles": ["Art.9"],
        "articles": [
            {
                "article": "Art.9",
                "verdict": "PASS",
                "evidence_uris": ["minio://x/T14"],
                "supporting_template_ids": ["T14_governance_findings"],
                "source_phase": "P5",
            }
        ],
        "kpi_summary": {
            "intake_completeness_score": 1.0,
            "completeness_score": 0.9,
            "regulatory_coverage_pct": 100.0,
        },
        "final_verdict": "PASS",
        "generated_at": "2025-01-01T00:00:00Z",
    }
    # may raise on unrelated additional properties; this is the smoke contract:
    try:
        utt.validate("T17_compliance_matrix", instance)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"valid T17 instance was rejected: {exc}")


def test_validate_rejects_missing_required_field():
    import jsonschema

    with pytest.raises(jsonschema.ValidationError):
        utt.validate("T17_compliance_matrix", {"engagement_id": "eng-y"})


# ---------------------------------------------------------------------------
# Jinja partials
# ---------------------------------------------------------------------------

def test_partial_env_finds_packaged_t17_partial():
    env = utt.partial_env()
    tmpl = env.get_template("T17_compliance_matrix.j2")
    assert tmpl is not None


def test_render_partial_t17_outputs_markdown_table():
    md = utt.render_partial("T17_compliance_matrix", {
        "engagement_id": "eng-x",
        "risk_tier": "high",
        "in_scope_articles": ["Art.9", "Art.43"],
        "final_verdict": "PASS",
        "articles": [
            {"article": "Art.9", "verdict": "PASS",
             "evidence_uris": ["minio://x/T14"]},
            {"article": "Art.43", "verdict": "PASS",
             "evidence_uris": ["minio://x/T05"]},
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


def test_version_is_semver():
    parts = utt.__version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
