"""T15's monitoring and logging evidence is what the provider's documents say, quoted.

Split from test_artefacts_quote_provider_documents.py (T-20260913-100); the
grounded answers come from the provider's documents (T-20260913-032/035/041).
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15 import T15_QUESTIONS, build_t15
from aaa.platform.evidence.contract import artefact_schema_errors
from aaa.tools.document_evidence import DOSSIER
from tests.unit.support.provider_documents import CGSA, DOSSIER_B, NOW, ev, provider_found


def test_t15_lists_only_operating_tools_when_the_provider_says_monitoring_is_unbuilt() -> None:
    """T15 lists only operating tools when the provider says monitoring is unbuilt."""
    t15 = build_t15("eng", DOSSIER_B, CGSA, NOW, provider_found())
    monitoring = t15["monitoring_evidence"]
    assert monitoring["monitoring_tools"] == [
        "performance metrics (post_market_monitoring_plan.txt)",
        "error monitoring (post_market_monitoring_plan.txt)"]
    assert monitoring["drift_detection_documented"] is False
    assert monitoring["performance_dashboards_documented"] is None
    assert t15["logging_evidence"]["automatic_logging_enabled"] is True
    assert "application logs 45 days" in t15["logging_evidence"]["log_retention_period"]
    assert t15["logging_evidence"]["log_integrity_controls"] is None
    assert t15["post_market_monitoring"]["incident_reporting_documented"] is True
    assert t15["post_market_monitoring"]["serious_incident_threshold_defined"] is None
    assert not artefact_schema_errors("T15_monitoring_logging_review", t15)


def test_t15_a_plan_that_describes_running_monitoring_lists_what_it_names() -> None:
    """T15 a plan that describes running monitoring lists what it names."""
    found = {"dashboards": ev("Weekly : Automated error-rate dashboard (MLflow)"),
             "drift": ev("PSI drift monitoring on top-10 features;", f"{DOSSIER}monitoring_measures"),
             # Art. 12 also needs a retention period (Art. 19(1), T-20260913-072).
             "log_retention": ev("Inference logs are retained for 13 months.")}
    t15 = build_t15("eng", DOSSIER_B, CGSA, NOW, found)
    monitoring = t15["monitoring_evidence"]
    assert monitoring["drift_detection_documented"] is True
    assert monitoring["performance_dashboards_documented"] is True
    assert "drift monitoring (Annex IV dossier, monitoring_measures)" in monitoring["monitoring_tools"]
    assert t15["art12_record_keeping"]["status"] == "PASS"


def test_t15_without_documents_claims_nothing() -> None:
    """T15 without documents claims nothing."""
    t15 = build_t15("eng", DOSSIER_B, CGSA, NOW)
    assert t15["monitoring_evidence"]["monitoring_tools"] == []
    assert t15["logging_evidence"]["automatic_logging_enabled"] is None
    assert t15["art72_post_market_plan"]["status"] == "PASS_WITH_OBSERVATIONS"
    assert build_t15("eng", {}, CGSA, NOW)["art72_post_market_plan"]["status"] == "FAIL"
    assert not artefact_schema_errors("T15_monitoring_logging_review", t15)


def test_t15_reads_a_per_event_log_as_automatic() -> None:
    """T15 reads a per event log as automatic."""
    from aaa.tools.document_evidence import gather_evidence

    dossier = {"logging_capabilities": "Per-prediction log: timestamp, hashed applicant_id, "
                                       "score, decision -- retained 10 years per Art. 12."}
    found = gather_evidence("", T15_QUESTIONS, declared=dossier)
    assert found["automatic_logging"] is not None
