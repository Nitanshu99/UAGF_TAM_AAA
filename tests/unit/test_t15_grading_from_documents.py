"""T15's Art. 12 / Art. 72 grades follow the documented elements (ISO/IEC 17021-1 grading).

Split from test_artefacts_quote_provider_documents.py (T-20260913-100); the
grounded answers come from the provider's documents (T-20260913-032/035/041).
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15 import build_t15
from tests.unit.support.provider_documents import CGSA, DOSSIER_B, NOW, ev, provider_found


def test_t15_grades_an_unbuilt_monitoring_system_and_an_unlogged_output_as_major() -> None:
    """ISO/IEC 17021-1 grading: a required element absent or not shown operating is FAIL."""
    t15 = build_t15("eng", DOSSIER_B, CGSA, NOW, provider_found())
    art12, art72 = t15["art12_record_keeping"], t15["art72_post_market_plan"]
    assert art12["status"] == art72["status"] == t15["overall_ops_verdict"] == "FAIL"
    assert "outputs are not recorded" in art12["rationale"] and "does not yet exist" in art12["rationale"]
    assert "not shown operating" in art72["rationale"]
    assert "annex_iv_dossier:monitoring_measures" in art72["evidence_refs"]
    assert any(o.startswith("Art. 72:") for o in t15["observations"])
    assert t15["hitl_required"] is True


def test_t15_a_gap_outside_the_output_log_is_minor() -> None:
    """T15 a gap outside the output log is minor."""
    found = {**provider_found(), "logging_gap": ev("Authentication log retention is not yet 90 days.")}
    assert build_t15("eng", DOSSIER_B, CGSA, NOW, found)["art12_record_keeping"]["status"] == (
        "PASS_WITH_OBSERVATIONS")


def test_t15_every_essential_element_evidenced_passes_and_one_missing_is_minor() -> None:
    """T15 every essential element evidenced passes and one missing is minor."""
    documented = {"accuracy": ev("Monthly AUC-ROC on production sample, threshold 0.78."),
                  "fairness": ev("Demographic parity delta by gender reviewed monthly."),
                  "field_data": ev("Deployer feedback is collected in a quarterly survey."),
                  "incident_reporting": ev("Serious incidents are reported per Article 73.")}
    assert build_t15("eng", DOSSIER_B, CGSA, NOW, documented)["art72_post_market_plan"][
        "status"] == "PASS"
    partial = {k: v for k, v in documented.items() if k != "field_data"}
    graded = build_t15("eng", DOSSIER_B, CGSA, NOW, partial)["art72_post_market_plan"]
    assert graded["status"] == "PASS_WITH_OBSERVATIONS" and "Art. 72(2)" in graded["rationale"]


def test_t15_a_declared_absence_outweighs_silence() -> None:
    """T15 a declared absence outweighs silence."""
    found = {"accuracy_absent": ev("Monthly : [PLANNED] Full model performance review (not yet operational)"),
             "fairness": ev("Demographic parity delta by gender reviewed monthly."),
             "field_data": ev("Deployer feedback is collected in a quarterly survey."),
             "incident_reporting": ev("Serious incidents are reported per Article 73.")}
    assert build_t15("eng", DOSSIER_B, CGSA, NOW, found)["art72_post_market_plan"]["status"] == "FAIL"
