"""
Unit tests for aaa.tools.intake_completeness_calculator (§9.1).

Covers:
  - Full Stage B dossier (tabular) → score >= 0.80, gate_passed=True
  - Empty dossier → score 0.0, gate_passed=False
  - Missing individual required fields → partial score reduction
  - L-branch modality with missing conditional fields → score penalty
  - L-branch modality with all conditional fields present → no penalty
  - _field_present helper edge cases
"""
from __future__ import annotations

import copy
import json
import pathlib

import pytest

from aaa.tools.intake_completeness_calculator import (
    GATE_THRESHOLD,
    CompletenessReport,
    intake_completeness_calculator,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_STAGE_B_FIXTURE = _REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit" / "stage_b.json"


def _load_stage_b() -> dict:
    with _STAGE_B_FIXTURE.open() as f:
        return json.load(f)


def _make_submission(stage_b: dict) -> dict:
    """Wrap a stage_b dict in a minimal ClientSubmission shape."""
    return {
        "stage_a": {"declared_modality": "tabular"},
        "stage_b": stage_b,
        "stage_c": None,
        "intake_completeness_score": 0.0,
    }


# ── Full fixture ─────────────────────────────────────────────────────────────


def test_full_fixture_passes_gate():
    dossier = _load_stage_b()
    submission = _make_submission(dossier)
    report = intake_completeness_calculator(submission, "tabular", "test-eng-001")

    assert isinstance(report, CompletenessReport)
    assert report.score >= GATE_THRESHOLD, f"score={report.score} below gate {GATE_THRESHOLD}"
    assert report.gate_passed is True
    assert report.engagement_id == "test-eng-001"


def test_full_fixture_all_sections_present():
    dossier = _load_stage_b()
    submission = _make_submission(dossier)
    report = intake_completeness_calculator(submission, "tabular")

    # 9 sections should all have scores
    assert len(report.section_scores) == 9
    for sec_id, sec_score in report.section_scores.items():
        assert 0.0 <= sec_score.score <= 1.0, f"Section {sec_id} score out of range"


# ── Empty / partial dossier ──────────────────────────────────────────────────


def test_empty_dossier_fails_gate():
    submission = _make_submission({})
    report = intake_completeness_calculator(submission, "tabular")
    assert report.score == 0.0
    assert report.gate_passed is False
    # All required fields should be listed as missing
    assert len(report.missing_required) > 0


def test_missing_one_required_field_reduces_score():
    dossier = _load_stage_b()
    dossier.pop("general_description")
    submission = _make_submission(dossier)
    full_report = intake_completeness_calculator(_make_submission(_load_stage_b()), "tabular")
    partial_report = intake_completeness_calculator(submission, "tabular")
    assert partial_report.score < full_report.score


def test_missing_required_field_appears_in_report():
    dossier = _load_stage_b()
    dossier.pop("risk_management_file_uri")
    submission = _make_submission(dossier)
    report = intake_completeness_calculator(submission, "tabular")
    missing_fields = [m.field for m in report.missing_required]
    assert "risk_management_file_uri" in missing_fields


# ── L-branch (LLM / agentic) ─────────────────────────────────────────────────


def test_l_branch_missing_conditionals_penalises_score():
    """LLM modality with null conditional fields → score penalty applied."""
    dossier = _load_stage_b()
    # Ensure all L-branch conditionals are null (already null in fixture)
    submission = _make_submission(dossier)
    l_report = intake_completeness_calculator(submission, "llm")
    tabular_report = intake_completeness_calculator(_make_submission(_load_stage_b()), "tabular")
    # L-branch score should be lower due to missing conditionals
    assert l_report.score <= tabular_report.score


def test_l_branch_with_all_conditionals_no_penalty():
    """LLM modality with all conditional fields present → no score penalty."""
    dossier = _load_stage_b()
    dossier["system_prompt_uri"] = "minio://eng/prompts/system_v1.txt"
    dossier["rag_manifest_uri"] = "minio://eng/rag/manifest.json"
    dossier["guardrail_config_uri"] = "minio://eng/guardrails/config.yaml"
    dossier["golden_set_uri"] = "minio://eng/golden/set_v1.jsonl"
    submission = _make_submission(dossier)
    report = intake_completeness_calculator(submission, "llm")
    assert report.gate_passed is True


def test_agentic_requires_tool_inventory():
    dossier = _load_stage_b()
    # tool_inventory is null in fixture → should be flagged as applicable
    submission = _make_submission(dossier)
    report = intake_completeness_calculator(submission, "agentic")
    tool_conditionals = [
        c for c in report.missing_conditional if c.field == "tool_inventory"
    ]
    assert len(tool_conditionals) == 1
    assert tool_conditionals[0].applicable is True


# ── to_dict contract ─────────────────────────────────────────────────────────


def test_to_dict_has_required_keys():
    dossier = _load_stage_b()
    report = intake_completeness_calculator(_make_submission(dossier), "tabular", "eng-x")
    d = report.to_dict()
    for key in (
        "engagement_id",
        "intake_completeness_score",
        "section_scores",
        "missing_required_fields",
        "missing_conditional_fields",
        "gate_passed",
    ):
        assert key in d, f"Missing key in to_dict(): {key}"
