"""Art. 12 is graded on log retention as well as declared gaps (T-20260913-072).

Case 03 documented logging and nothing about retention or integrity, and T15 said
PASS "no logging gap declared" beside its own null retention and integrity fields.
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.grading.art12 import grade_art12
from aaa.tools.document_evidence import Evidence

_LOGGING = "Every inference is logged with timestamp, input hash and anomaly score."


def _quote(text: str) -> Evidence:
    return Evidence(text, "minio://eng/client_docs/plan.txt", "plan.txt")


def test_no_retention_period_is_a_minor_nonconformity_citing_art_19() -> None:
    grade = grade_art12(_LOGGING, {"logging_gap": None, "log_retention": None, "log_integrity": None})
    assert grade.status == "PASS_WITH_OBSERVATIONS"
    assert "Art. 19(1)" in grade.rationale and "integrity" in grade.rationale
    assert grade.observations == [
        "Art. 12: no log retention period evidenced; Art. 19(1) requires automatically "
        "generated logs to be kept for at least six months"]


def test_retention_and_integrity_evidenced_with_no_gap_pass() -> None:
    grade = grade_art12(_LOGGING, {"logging_gap": None,
                                   "log_retention": _quote("Logs are retained for 24 months."),
                                   "log_integrity": _quote("Logs are append-only.")})
    assert grade.status == "PASS" and not grade.observations


def test_an_output_event_gap_still_fails() -> None:
    grade = grade_art12(_LOGGING, {"logging_gap": _quote("Model predictions are not yet logged."),
                                   "log_retention": _quote("Logs are retained for 24 months.")})
    assert grade.status == "FAIL"


def test_articles_that_do_not_bind_the_tier_are_not_applicable() -> None:
    """Case 02 (limited risk) had Art. 12/17/72 graded as obligations; the Verifier refused T15."""
    from aaa.agents.tier2.governance_agent.t15 import build_t15
    from aaa.platform.evidence.contract import artefact_schema_errors
    from aaa.tools.cgsa_ingest import IngestResult

    dossier = {"logging_capabilities": _LOGGING, "monitoring_measures": "Weekly error dashboard."}
    limited = build_t15("eng", dossier, IngestResult(payload={}, state_delta={}), "2026-09-13T00:00:00Z",
                        scope={"risk_tier": "limited"})
    for block in ("art12_record_keeping", "art17_qms", "art72_post_market_plan"):
        assert limited[block]["status"] == "NOT_APPLICABLE"
        assert "'limited'" in limited[block]["rationale"]
    assert limited["overall_ops_verdict"] == "NOT_APPLICABLE"
    assert not any("Art. 12" in o or "Art. 72" in o for o in limited["observations"])
    assert artefact_schema_errors("T15_monitoring_logging_review", limited) == []

    high = build_t15("eng", dossier, IngestResult(payload={}, state_delta={}), "2026-09-13T00:00:00Z",
                     scope={"risk_tier": "high"})
    assert high["art12_record_keeping"]["status"] == "PASS_WITH_OBSERVATIONS"
    unknown = build_t15("eng", dossier, IngestResult(payload={}, state_delta={}), "2026-09-13T00:00:00Z")
    assert unknown["art12_record_keeping"]["status"] != "NOT_APPLICABLE"


def test_t14_says_which_self_assessed_articles_do_not_bind() -> None:
    """Case 02's T14 carried the CGSA's high-risk article mapping unqualified."""
    from aaa.agents.tier2.governance_agent.scope_note import cgsa_scope_note

    payload = {"eu_ai_act_compliance_matrix": {"article_9": {}, "article_13": {}, "article_72": {}}}
    note = cgsa_scope_note(payload, {"risk_tier": "limited"})
    assert "Art.9, Art.72" in note and "Art.13" not in note
    assert cgsa_scope_note(payload, {"risk_tier": "high"}) == ""
    assert cgsa_scope_note(payload, {}) == ""


def test_the_low_confidence_reason_states_each_controls_own_confidence() -> None:
    """Case 04: '2 CGSA controls flagged low-confidence (<0.60)' beside 0.65 and 0.70."""
    from aaa.agents.tier2.governance_agent.hitl import low_confidence_reason

    reason = low_confidence_reason([{"control_id": "C15", "confidence": 0.65},
                                    {"control_id": "C21", "confidence": 0.7}])
    assert "C15 (0.65), C21 (0.70)" in reason and "(<0.60)" not in reason


def test_a_control_without_an_applicable_constraint_is_never_below_threshold() -> None:
    """``threshold_score or 3`` judged unconstrained controls against an assumed 3."""
    from aaa.agents.tier2.governance_agent.below import _below

    assert not _below({"maturity_score": 1, "hard_constraint": {"applicable": False,
                                                                 "threshold_score": None}})
    assert not _below({"maturity_score": 1})
    assert _below({"maturity_score": 2, "hard_constraint": {"applicable": True, "threshold_score": 3}})
