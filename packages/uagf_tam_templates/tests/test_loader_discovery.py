"""Smoke tests for template discovery and schema loading."""
from __future__ import annotations

import pathlib

import pytest
import uagf_tam_templates as utt


def test_list_templates_contains_t01a_to_t18():
    ids = utt.list_templates()
    # ARCHITECTURE §4A guarantees T01a + T01b + T01c + T02..T16 + T17 + T18.
    for prefix in ("T01a_stage_a_triage", "T01b_annex_iv_dossier",
                   "T01c_intake_completeness_report", "T02_system_card",
                   "T17_compliance_matrix", "T18_audit_report"):
        assert prefix in ids, f"missing template: {prefix}"
    assert len(ids) >= 18


def test_schema_path_returns_existing_file():
    p = utt.schema_path("T17_compliance_matrix")
    assert isinstance(p, pathlib.Path) and p.is_file()


def test_schema_path_raises_for_unknown_template():
    with pytest.raises(utt.SchemaNotFoundError):
        utt.schema_path("T99_does_not_exist")


def test_load_schema_returns_jsonschema_draft7():
    schema = utt.load_schema("T17_compliance_matrix")
    assert schema["$schema"].endswith("draft-07/schema#")
    assert "properties" in schema and "required" in schema


def test_load_schema_is_cached():
    a = utt.load_schema("T17_compliance_matrix")
    b = utt.load_schema("T17_compliance_matrix")
    assert a is b  # lru_cache hit


def test_version_is_semver():
    parts = utt.__version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
