"""Round-trip tests for audit-result persistence (writer + reader)."""
from __future__ import annotations

import json
from typing import Any

from tests.unit.support.data_store_fixtures import isolated_data_dir  # noqa: F401


def test_save_result_creates_all_four_files():
    from aaa.data.paths import (
        ARTEFACTS_FILE,
        AUDIT_RESULT_FILE,
        COMPLIANCE_MATRIX_FILE,
        FINDINGS_FILE,
        results_dir,
    )
    from aaa.data.writer import save_result

    final_state: dict[str, Any] = {
        "final_verdict": "PASS",
        "intake_completeness_score": 0.92,
        "completeness_score": 0.95,
        "regulatory_coverage_pct": 93.0,
        "material_findings_count": 0,
        "possibly_material_findings_count": 1,
        "auditor_opinion": "Satisfactory",
        "art43_decision": {"procedure": "internal_control", "rationale": "ok"},
        "blocking_findings": [],
        "positive_findings": [{"id": "pf1"}],
        "remediation_roadmap": [],
        "compliance_matrix": {"Art.5": "PASS", "Art.10": "PASS"},
        "phase_artefacts": {"T02_system_card": {"uri": "mem://eng-w4/T02"}},
    }
    save_result("eng-w4", final_state)
    rdir = results_dir("eng-w4")
    for fname in [AUDIT_RESULT_FILE, ARTEFACTS_FILE, FINDINGS_FILE,
                  COMPLIANCE_MATRIX_FILE]:
        assert (rdir / fname).exists(), f"{fname} not created"
    assert json.loads((rdir / AUDIT_RESULT_FILE).read_text())["final_verdict"] == "PASS"
