"""The S5 dialect translation — what it must recover, and what it must not invent.

S5 ships ``schema_version: "s5-aaa-adapter-v1.0"``, which is not the ``1.0.0``
contract this repo pins. The first real payload failed validation in hundreds of
places, so the GovernanceAgent escalated before reading a control and no
governance finding reached an article — re-deriving Mariposa's matrix from it
turned Art. 17, whose FAIL rests on governance alone, into a **PASS**.

These tests fix the two halves of the repair: the translation recovers what S5
actually sent, and it leaves alone every payload that already speaks the contract.
"""
from __future__ import annotations

import copy

from aaa.tools.cgsa_ingest.s5.dialect import adapt_s5_dialect, is_s5_dialect
from aaa.tools.cgsa_ingest.s5.fields import control_summary, coverage_pct

_CONTROL = {
    "control_id": "C34", "control_name": "Post-Market Monitoring Plan",
    "final_maturity_score": 1, "threshold_score": 3, "gap_severity": "critical",
    "gap_detail": "Score 1 below threshold 3. Produce a monitoring plan.",
    "eu_ai_act_articles": ["Article 17", "Article 72"],
    "evidence_metadata": {"source_document": "questionnaire.pdf"},
}
_PASSING = {
    "control_id": "C29", "control_name": "Human Oversight",
    "final_maturity_score": 3, "threshold_score": 3,
    "gap_severity": None, "gap_detail": None,
    "eu_ai_act_articles": ["Article 14"],
    "evidence_metadata": {"source_document": "questionnaire.pdf"},
}


def _payload() -> dict:
    """A minimal payload in the S5 dialect, carrying both a gap and a pass."""
    return copy.deepcopy({
        "schema_version": "s5-aaa-adapter-v1.0",
        "domains": [{"domain_id": "D6", "controls": [_CONTROL, _PASSING]}],
        "overall_scores": {"csp_satisfiable": False},
        "remediation_roadmap": [
            {"rank": 1, "control_id": "C34",
             "control_name": "Post-Market Monitoring Plan", "gap_severity": "critical",
             "current_score": 1, "target_score": 3, "eu_ai_act_article": "Article 17",
             "action": "Write and own a post-market monitoring plan."}],
        "hard_constraint_results": {
            "violated_constraints": [
                {"control_id": "C34", "final_score": 1, "threshold": 3}],
            "satisfied_constraints": [
                {"control_id": "C29", "final_score": 3, "threshold": 3}]},
        "eu_ai_act_compliance_matrix": {
            "article_9": {"controls_mapped": 1, "controls_satisfied": 0,
                          "controls": [{"control_id": "C34", "satisfied": False}]},
            "article_10": {"controls_mapped": 1, "controls_satisfied": 1,
                           "controls": [{"control_id": "C29", "satisfied": True}]},
            "article_13": {"controls_mapped": 0, "controls_satisfied": 0, "controls": []}},
        "aaa_phase5_handoff": {
            "blocking_findings": [
                {"control_id": "C34", "finding_type": "hard_constraint_violation",
                 "severity": "critical",
                 "description": "Hard constraint violated for control C34."}],
            "low_confidence_controls": [
                {"control_id": "C34", "control_name": "Post-Market Monitoring Plan",
                 "confidence": 0.5, "evidence_found": False}]},
    })


# --------------------------------------------------------------------------
# it only touches the dialect it was written for
# --------------------------------------------------------------------------
def test_the_dialect_is_recognised_by_the_version_it_declares():
    """Gating on the declared version keeps a conforming producer untouched."""
    assert is_s5_dialect(_payload())
    assert not is_s5_dialect({"schema_version": "1.0.0"})
    assert not is_s5_dialect({})
    assert not is_s5_dialect(None)


def test_the_input_payload_is_not_mutated():
    """The caller keeps what S5 actually sent, for the evidence trail."""
    payload = _payload()
    before = copy.deepcopy(payload)
    adapt_s5_dialect(payload)
    assert payload == before


# --------------------------------------------------------------------------
# the article mapping — the failure that turned a FAIL into a PASS
# --------------------------------------------------------------------------
def test_every_blocking_finding_is_given_the_article_its_control_names():
    """Without this, no governance gap reaches the compliance matrix at all."""
    finding = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["blocking_findings"][0]
    assert finding["eu_ai_act_article"] == "Article 17"
    assert finding["control_name"] == "Post-Market Monitoring Plan"


def test_the_finding_text_comes_from_the_control_not_the_counter():
    """The dialect's own `description` is boilerplate repeated across findings."""
    finding = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["blocking_findings"][0]
    assert finding["finding"] == _CONTROL["gap_detail"]
    assert "Hard constraint violated for control" not in finding["finding"]


def test_the_remediation_action_is_joined_from_the_roadmap():
    """The action lives in the roadmap, keyed by the control it remediates."""
    finding = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["blocking_findings"][0]
    assert finding["remediation_action"] == "Write and own a post-market monitoring plan."


# --------------------------------------------------------------------------
# the rest of the contract's required fields
# --------------------------------------------------------------------------
def test_control_id_lists_are_recovered_from_the_counts():
    """The dialect reports counts and keeps the identities in `controls`."""
    matrix = adapt_s5_dialect(_payload())["eu_ai_act_compliance_matrix"]
    assert matrix["article_9"]["controls_mapped"] == ["C34"]
    assert matrix["article_9"]["controls_satisfied"] == []
    assert matrix["article_10"]["controls_satisfied"] == ["C29"]


def test_a_passing_control_still_gets_an_evidence_summary():
    """S5 writes prose only for gaps, so a satisfied control carries none."""
    summary = control_summary(_PASSING)
    assert summary is not None and "3" in summary and "questionnaire.pdf" in summary


def test_coverage_is_computed_over_the_three_articles_the_contract_names():
    """Arts. 9/10/13 only — not the dialect's all-38-control percentage."""
    matrix = adapt_s5_dialect(_payload())["eu_ai_act_compliance_matrix"]
    assert coverage_pct(matrix) == 50.0     # 1 of 2 mapped controls satisfied


def test_a_low_confidence_control_says_why_it_was_flagged():
    """`evidence_found` separates "no document at all" from "document said little"."""
    entry = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["low_confidence_controls"][0]
    assert "No supporting document" in entry["flag_reason"]


def test_both_hard_constraint_lists_are_completed():
    """Violated and satisfied records both need their control's name, scores and article."""
    results = adapt_s5_dialect(_payload())["hard_constraint_results"]
    violated = results["violated_constraints"][0]
    assert violated["required_score"] == 3 and violated["actual_score"] == 1
    assert violated["eu_ai_act_article"] == "Article 17"
    assert violated["violation_description"] == _CONTROL["gap_detail"]
    assert results["satisfied_constraints"][0]["control_name"] == "Human Oversight"


# --------------------------------------------------------------------------
# it derives, it does not invent
# --------------------------------------------------------------------------
def test_a_field_with_no_source_is_left_absent_rather_than_filled():
    """An underivable field must still fail validation, not pass on a placeholder."""
    payload = _payload()
    payload["domains"][0]["controls"] = [{"control_id": "C99"}]   # no scores, no articles
    payload["aaa_phase5_handoff"]["blocking_findings"] = [{"control_id": "C99"}]
    finding = adapt_s5_dialect(payload)["aaa_phase5_handoff"]["blocking_findings"][0]
    assert "eu_ai_act_article" not in finding
    assert "finding" not in finding


def test_values_the_payload_already_carries_are_never_overwritten():
    """The translation fills gaps; it does not restate what S5 chose to say."""
    payload = _payload()
    payload["aaa_phase5_handoff"]["blocking_findings"][0]["finding"] = "S5 said this."
    finding = adapt_s5_dialect(payload)["aaa_phase5_handoff"]["blocking_findings"][0]
    assert finding["finding"] == "S5 said this."


# --------------------------------------------------------------------------
# end to end, against the contract itself
# --------------------------------------------------------------------------
#: Every field the translation is responsible for filling. An error naming one
#: of these is the translation's failure; anything else is the fixture's.
_ADAPTED_FIELDS = ("evidence_summary", "flag_reason", "finding", "eu_ai_act_article",
                   "remediation_action", "control_name", "required_score",
                   "actual_score", "violation_description", "controls_mapped",
                   "controls_satisfied", "eu_ai_act_coverage_pct")


def test_no_field_the_translation_owns_still_fails_validation():
    """cgsa_ingest validates *after* translating, so Phase 5 no longer escalates.

    Matched on the validator's exact "is a required property" phrasing: an error
    that dumps the offending object quotes every field name inside it, so a
    substring test over the whole message reports fixture gaps as mine.
    """
    from aaa.tools.cgsa_ingest import cgsa_ingest
    result = cgsa_ingest(_payload(), phase1_risk_tier="high", strict=False)
    missing = {f"'{field}' is a required property" for field in _ADAPTED_FIELDS}
    mine = [e for e in result.schema_errors
            if any(m in str(e) for m in missing)]
    assert mine == [], mine


# --------------------------------------------------------------------------
# every article a control binds, not just the first
# --------------------------------------------------------------------------
def test_a_control_binding_two_articles_reaches_both():
    """The false PASS this prevents, stated as an assertion.

    C34 ("no monitoring plan", maturity 1 of 3) names Articles 9 and 72. Filed
    under Article 9 alone — which is what taking ``eu_ai_act_articles[0]`` did —
    **Art. 72 was admitted "with no findings raised"** on the 2026-09-10 MiniMax
    run. On the real export 24 of 38 controls name more than one article, and
    sixteen were reachable only as a non-first entry.
    """
    from aaa.tools.findings import articles_for
    control = {"control_id": "C34", "control_name": "Post-Market Monitoring Plan",
               "final_maturity_score": 1, "threshold_score": 3,
               "gap_detail": "Score 1 below threshold 3. Create a monitoring plan.",
               "eu_ai_act_articles": ["Article 9", "Article 72"]}
    payload = _payload()
    payload["domains"][0]["controls"] = [control]
    payload["aaa_phase5_handoff"]["blocking_findings"] = [
        {"control_id": "C34", "severity": "critical",
         "description": "Hard constraint violated for control C34."}]
    finding = adapt_s5_dialect(payload)["aaa_phase5_handoff"]["blocking_findings"][0]
    assert finding["eu_ai_act_article"] == "Article 9", "the contract's singular field"
    assert articles_for(finding) == ["Art.9", "Art.72"], "both articles must be indexed"


def test_a_single_article_control_is_unchanged():
    """The common case must not gain an empty plural key or lose its singular."""
    from aaa.tools.findings import articles_for
    finding = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["blocking_findings"][0]
    assert articles_for(finding) == ["Art.17", "Art.72"]


# --------------------------------------------------------------------------
# what the Mariposa wizard run's Verifier found missing (2026-09-14)
# --------------------------------------------------------------------------
def test_a_blocking_finding_keeps_its_controls_gap_severity():
    """T-20260914-057: the roadmap graded it critical while T14's finding read null."""
    finding = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["blocking_findings"][0]
    assert finding["gap_severity"] == "critical"
    payload = _payload()
    payload["domains"][0]["controls"][0]["gap_severity"] = None
    assert "gap_severity" not in adapt_s5_dialect(payload)["aaa_phase5_handoff"]["blocking_findings"][0]


def test_controls_meeting_their_threshold_become_positive_findings():
    """T-20260914-058: C29 meets 3 of 3, so the hand-off names it; C34 does not."""
    positive = adapt_s5_dialect(_payload())["aaa_phase5_handoff"]["positive_findings"]
    assert [(p["control_id"], p["maturity_score"]) for p in positive] == [("C29", 3)]
    assert positive[0]["control_name"] == "Human Oversight"
    assert "Meets its threshold at maturity 3 of 3" in positive[0]["finding"]


def test_positive_findings_the_payload_ships_are_kept():
    """Derived only when S5 sent none."""
    payload = _payload()
    shipped = [{"control_id": "C29", "control_name": "Human Oversight", "maturity_score": 3,
                "finding": "S5 said this."}]
    payload["aaa_phase5_handoff"]["positive_findings"] = shipped
    assert adapt_s5_dialect(payload)["aaa_phase5_handoff"]["positive_findings"] == shipped
