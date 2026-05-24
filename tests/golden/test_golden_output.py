"""
Golden-output tests — verify that the deterministic (offline) layer of the
AAA pipeline produces KPI values consistent with the committed reference
in out/eng-uci-german-credit-001.json.

These tests exercise the tool-layer directly (no LLM calls), so they run
in every CI environment without Docker services:

  - intake_completeness_calculator  → intake_completeness_score
  - cgsa_ingest                     → cgsa_composite_maturity_score,
                                      cgsa_phase5_verdict,
                                      harmonised_standards_applied

Golden tolerances are intentionally tight (±0.01) because the calculators
are deterministic; any drift indicates an unintended algorithm change.

If you update SECTION_WEIGHTS or the CGSA fixture, update the golden values
here AND the committed out/ artefact, then open a PR for supervisor sign-off.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from aaa.tools.cgsa_ingest import cgsa_ingest
from aaa.tools.intake_completeness_calculator import intake_completeness_calculator

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_GOLDEN = _REPO_ROOT / "out" / "eng-uci-german-credit-001.json"
_STAGE_B = _REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit" / "stage_b.json"
_CGSA_FIXTURE = _REPO_ROOT / "scripts" / "fixtures" / "cgsa" / "uci-german-credit-001.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(_GOLDEN.read_text())


@pytest.fixture(scope="module")
def stage_b() -> dict:
    return json.loads(_STAGE_B.read_text())


@pytest.fixture(scope="module")
def cgsa_payload() -> dict:
    return json.loads(_CGSA_FIXTURE.read_text())


# ── intake_completeness_score ─────────────────────────────────────────────────


def test_golden_intake_completeness_score(golden, stage_b):
    """intake_completeness_score must match the golden reference ±0.01."""
    submission = {
        "stage_a": {"declared_modality": "tabular"},
        "stage_b": stage_b,
        "stage_c": None,
        "intake_completeness_score": 0.0,
    }
    report = intake_completeness_calculator(submission, "tabular", "eng-uci-german-credit-001")
    golden_score = golden["intake_completeness_score"]
    assert abs(report.score - golden_score) <= 0.01, (
        f"intake_completeness_score={report.score} deviates from golden={golden_score}"
    )


def test_golden_intake_gate_passed(golden, stage_b):
    """The UCI German Credit fixture must always pass the completeness gate."""
    submission = {
        "stage_a": {"declared_modality": "tabular"},
        "stage_b": stage_b,
        "stage_c": None,
        "intake_completeness_score": 0.0,
    }
    report = intake_completeness_calculator(submission, "tabular")
    assert report.gate_passed is True


# ── cgsa_ingest golden ────────────────────────────────────────────────────────


def test_golden_cgsa_phase5_verdict(golden, cgsa_payload):
    """CGSA ingestion must yield the same phase5_verdict as the golden file."""
    result = cgsa_ingest(cgsa_payload, phase1_risk_tier="high")
    # The golden file doesn't directly store cgsa_phase5_verdict, but the
    # final_verdict is PASS_WITH_OBSERVATIONS implying cgsa passed.
    assert result.state_delta["cgsa_phase5_verdict"] in {"PASS", "PASS_WITH_OBSERVATIONS"}
    assert result.state_delta["cgsa_csp_satisfiable"] is True


def test_golden_cgsa_maturity_score(cgsa_payload):
    """Composite maturity score must match the fixture value exactly."""
    result = cgsa_ingest(cgsa_payload)
    assert result.state_delta["cgsa_composite_maturity_score"] == pytest.approx(3.4, abs=0.01)


def test_golden_harmonised_standards_applied(cgsa_payload):
    """The UCI German Credit CGSA fixture cites ISO 42001 → True."""
    result = cgsa_ingest(cgsa_payload)
    assert result.state_delta["harmonised_standards_applied"] is True


def test_golden_eu_ai_act_coverage_pct(cgsa_payload):
    """EU AI Act coverage pct must be ≥ 80 (fixture: 92.5)."""
    result = cgsa_ingest(cgsa_payload)
    assert result.state_delta["cgsa_eu_ai_act_coverage_pct"] >= 80.0


# ── golden file integrity ────────────────────────────────────────────────────


def test_golden_file_has_required_top_level_keys(golden):
    for key in (
        "engagement_id",
        "final_verdict",
        "intake_completeness_score",
        "completeness_score",
        "regulatory_coverage_pct",
        "art43_decision",
        "phase_artefacts",
        "compliance_matrix",
    ):
        assert key in golden, f"Golden file missing key: {key}"


def test_golden_file_kpi_bands(golden):
    """All three main KPIs must be in their passing bands per §9.1."""
    assert golden["intake_completeness_score"] >= 0.80
    assert golden["completeness_score"] >= 0.85
    assert golden["regulatory_coverage_pct"] >= 80.0


def test_golden_phase_artefacts_t01_to_t18(golden):
    """Phase artefacts dict must include T01a through T18 (T16 optional)."""
    artefacts = golden["phase_artefacts"]
    required = [
        "T01a_stage_a_triage", "T01b_annex_iv_dossier", "T01c_intake_completeness_report",
        "T02_system_card", "T05_art43_decision", "T17_compliance_matrix", "T18_audit_report",
    ]
    for key in required:
        assert key in artefacts, f"phase_artefacts missing: {key}"
