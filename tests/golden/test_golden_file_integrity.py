"""Golden-file structural integrity: required keys, KPI bands, artefacts."""
from __future__ import annotations

from tests.golden.support.golden_fixtures import golden  # noqa: F401


def test_golden_file_has_required_top_level_keys(golden):  # noqa: F811
    for key in ("engagement_id", "final_verdict", "intake_completeness_score",
                "completeness_score", "regulatory_coverage_pct", "art43_decision",
                "phase_artefacts", "compliance_matrix"):
        assert key in golden, f"Golden file missing key: {key}"


def test_golden_file_kpi_bands(golden):  # noqa: F811
    """All three main KPIs must be in their passing bands per §9.1."""
    assert golden["intake_completeness_score"] >= 0.80
    assert golden["completeness_score"] >= 0.85
    assert golden["regulatory_coverage_pct"] >= 80.0


def test_golden_phase_artefacts_t01_to_t18(golden):  # noqa: F811
    """Phase artefacts dict must include T01a through T18 (T16 optional)."""
    artefacts = golden["phase_artefacts"]
    required = [
        "T01a_stage_a_triage", "T01b_annex_iv_dossier",
        "T01c_intake_completeness_report", "T02_system_card",
        "T05_art43_decision", "T17_compliance_matrix", "T18_audit_report",
    ]
    for key in required:
        assert key in artefacts, f"phase_artefacts missing: {key}"
