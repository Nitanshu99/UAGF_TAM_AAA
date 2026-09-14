"""intake_completeness: full-fixture pass, empty/partial dossier, to_dict."""
from __future__ import annotations

from aaa.tools.intake_completeness_calculator import (
    GATE_THRESHOLD,
    CompletenessReport,
    intake_completeness_calculator,
)
from tests.unit.support.intake_completeness_fixture import load_stage_b, make_submission


def test_full_fixture_passes_gate():
    report = intake_completeness_calculator(
        make_submission(load_stage_b()), "tabular", "test-eng-001")
    assert isinstance(report, CompletenessReport)
    assert report.score >= GATE_THRESHOLD, f"score={report.score} below {GATE_THRESHOLD}"
    assert report.gate_passed is True
    assert report.engagement_id == "test-eng-001"


def test_full_fixture_all_sections_present():
    report = intake_completeness_calculator(make_submission(load_stage_b()), "tabular")
    assert len(report.section_scores) == 9
    for sec_id, sec_score in report.section_scores.items():
        assert 0.0 <= sec_score.score <= 1.0, f"Section {sec_id} score out of range"


def test_empty_dossier_fails_gate():
    report = intake_completeness_calculator(make_submission({}), "tabular")
    assert report.score == 0.0
    assert report.gate_passed is False
    assert len(report.missing_required) > 0


def test_missing_one_required_field_reduces_score():
    dossier = load_stage_b()
    dossier.pop("general_description")
    full = intake_completeness_calculator(make_submission(load_stage_b()), "tabular")
    partial = intake_completeness_calculator(make_submission(dossier), "tabular")
    assert partial.score < full.score


def test_missing_required_field_appears_in_report():
    dossier = load_stage_b()
    dossier.pop("risk_management_file_uri")
    report = intake_completeness_calculator(make_submission(dossier), "tabular")
    assert "risk_management_file_uri" in [m.field for m in report.missing_required]


def test_to_dict_has_required_keys():
    report = intake_completeness_calculator(
        make_submission(load_stage_b()), "tabular", "eng-x")
    d = report.to_dict()
    for key in ("engagement_id", "intake_completeness_score", "section_scores",
                "missing_required_fields", "missing_conditional_fields", "gate_passed"):
        assert key in d, f"Missing key in to_dict(): {key}"
