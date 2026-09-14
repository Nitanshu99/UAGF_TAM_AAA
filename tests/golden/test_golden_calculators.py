"""Golden tests for the deterministic calculators (no LLM calls).

Golden tolerances are intentionally tight (±0.01) because the calculators are
deterministic; any drift indicates an unintended algorithm change.  If you
update SECTION_WEIGHTS or the CGSA fixture, update the golden values here AND
the committed out/ artefact, then open a PR for supervisor sign-off.
"""
from __future__ import annotations

import pytest

from aaa.tools.cgsa_ingest import cgsa_ingest
from aaa.tools.intake_completeness_calculator import intake_completeness_calculator
from tests.golden.support.golden_fixtures import cgsa_payload, golden, stage_b  # noqa: F401


def _submission(stage_b_payload: dict) -> dict:
    return {"stage_a": {"declared_modality": "tabular"}, "stage_b": stage_b_payload,
            "stage_c": None, "intake_completeness_score": 0.0}


def test_golden_intake_completeness_score(golden, stage_b):  # noqa: F811
    """intake_completeness_score must match the golden reference ±0.01."""
    report = intake_completeness_calculator(
        _submission(stage_b), "tabular", "eng-uci-german-credit-001")
    golden_score = golden["intake_completeness_score"]
    assert abs(report.score - golden_score) <= 0.01, (
        f"intake_completeness_score={report.score} deviates from golden={golden_score}")


def test_golden_intake_gate_passed(golden, stage_b):  # noqa: F811
    """The UCI German Credit fixture must always pass the completeness gate."""
    assert intake_completeness_calculator(_submission(stage_b), "tabular").gate_passed is True


def test_golden_cgsa_phase5_verdict(golden, cgsa_payload):  # noqa: F811
    """CGSA ingestion must yield the same phase5_verdict as the golden file."""
    result = cgsa_ingest(cgsa_payload, phase1_risk_tier="high")
    assert result.state_delta["cgsa_phase5_verdict"] in {"PASS", "PASS_WITH_OBSERVATIONS"}
    assert result.state_delta["cgsa_csp_satisfiable"] is True


def test_golden_cgsa_maturity_score(cgsa_payload):  # noqa: F811
    """Composite maturity score must match the fixture value exactly."""
    result = cgsa_ingest(cgsa_payload)
    assert result.state_delta["cgsa_composite_maturity_score"] == pytest.approx(3.4, abs=0.01)


def test_golden_harmonised_standards_applied(cgsa_payload):  # noqa: F811
    """The UCI German Credit CGSA fixture cites ISO 42001 → True."""
    assert cgsa_ingest(cgsa_payload).state_delta["harmonised_standards_applied"] is True


def test_golden_eu_ai_act_coverage_pct(cgsa_payload):  # noqa: F811
    """EU AI Act coverage pct must be ≥ 80 (fixture: 92.5)."""
    assert cgsa_ingest(cgsa_payload).state_delta["cgsa_eu_ai_act_coverage_pct"] >= 80.0
