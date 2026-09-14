"""Round-trip test for the merged full-result view."""
from __future__ import annotations

from tests.unit.support.data_store_fixtures import isolated_data_dir  # noqa: F401


def test_load_full_result():
    from aaa.data.reader import load_full_result
    from aaa.data.writer import save_result

    save_result("eng-r3", {
        "final_verdict": "FAIL",
        "intake_completeness_score": 0.6,
        "completeness_score": 0.5,
        "regulatory_coverage_pct": 40.0,
        "material_findings_count": 2,
        "possibly_material_findings_count": 0,
        "auditor_opinion": None,
        "art43_decision": None,
        "blocking_findings": [{"id": "bf1"}],
        "positive_findings": [],
        "remediation_roadmap": [{"action": "fix data"}],
        "compliance_matrix": {"Art.5": "PENDING"},
        "phase_artefacts": {},
    })
    full = load_full_result("eng-r3")
    assert full is not None
    assert full["final_verdict"] == "FAIL"
    assert "findings" in full
    assert "compliance_matrix" in full
    assert "artefacts" in full
