"""Fix 21 — a verdict may cite only the artefacts the Verifier admitted (P7).

The state below is the post-fix run's own shape: ``T02`` admitted and citing
Art. 13, ``T09``/``T10``/``T11`` sent back for rerun, ``T06`` escalated, and the
two Stage-B intake artefacts present but never critiqued.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry
from aaa.agents.tier1.phases.compliance_matrix.rationale import _exclusion_note, _rationale
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import (
    _candidate_tids,
    _excluded_tids,
    _supporting_tids,
)
from aaa.platform.state.admission import admitted_artefacts
from aaa.tools.hitl_review import build_hitl_review_packet

_CRITIQUES = {
    "T02_system_card": {"verdict": "accept_with_notes",
                        "article_citations": ["Art.5", "Art.13"]},
    "T06_datasheet_for_datasets": {"verdict": "escalate_hitl",
                                   "article_citations": ["Art.10"]},
    "T07_data_quality_report": {"verdict": "accept_with_notes",
                                "article_citations": ["Art.10"]},
    "T09_model_card": {"verdict": "rerun", "article_citations": ["Art.13", "Art.15"]},
    "T10_explainability_report": {"verdict": "rerun", "article_citations": ["Art.13"]},
    "T11_robustness_report": {"verdict": "rerun", "article_citations": ["Art.15"]},
}

_ARTEFACTS = ("T01b_annex_iv_dossier", "T01c_intake_completeness_report",
              "T02_system_card", "T06_datasheet_for_datasets", "T07_data_quality_report",
              "T09_model_card", "T10_explainability_report", "T11_robustness_report")


def _state(**overrides: object) -> dict:
    """The run's critique/artefact shape, as the compliance-matrix node saw it."""
    state: dict = {
        "engagement_id": "eng-test",
        "verifier_critiques": {k: dict(v) for k, v in _CRITIQUES.items()},
        "phase_artefacts": {tid: {"uri": f"minio://e/p/{tid}.json"} for tid in _ARTEFACTS},
        "blocking_findings": [],
        "compliance_matrix": {},
    }
    state.update(overrides)
    return state


# --------------------------------------------------------------------------
# the predicate
# --------------------------------------------------------------------------
def test_both_admitting_verdicts_admit_and_no_others_do():
    """``accept`` and ``accept_with_notes`` admit; rerun and escalate_hitl do not."""
    state = _state()
    state["verifier_critiques"]["T14_governance_findings"] = {"verdict": "accept"}
    admitted = admitted_artefacts(state)
    assert {"T02_system_card", "T07_data_quality_report",
            "T14_governance_findings"} <= admitted
    assert admitted.isdisjoint({"T06_datasheet_for_datasets", "T09_model_card",
                                "T10_explainability_report", "T11_robustness_report"})


def test_an_unverified_artefact_is_not_admitted():
    """Fix 20's ``unverified`` is a check that did not run, so it admits nothing."""
    state = _state()
    state["verifier_critiques"]["T15_monitoring_logging_review"] = {"verdict": "unverified"}
    assert "T15_monitoring_logging_review" not in admitted_artefacts(state)


def test_the_uncritiqued_intake_artefacts_are_admitted_by_presence():
    """The phase pipeline never critiques Stage B, so presence is the only signal."""
    assert {"T01b_annex_iv_dossier",
            "T01c_intake_completeness_report"} <= admitted_artefacts(_state())


def test_an_intake_artefact_the_verifier_rejected_is_not_admitted():
    """Presence is a default, not an override: a critique that arrives governs."""
    state = _state()
    state["verifier_critiques"]["T01b_annex_iv_dossier"] = {"verdict": "rerun"}
    assert "T01b_annex_iv_dossier" not in admitted_artefacts(state)


def test_an_absent_intake_artefact_admits_nothing():
    """Nothing is admitted on a template id the engagement never produced."""
    state = _state(phase_artefacts={})
    assert admitted_artefacts(state).isdisjoint(
        {"T01b_annex_iv_dossier", "T01c_intake_completeness_report"})


# --------------------------------------------------------------------------
# the evidence list
# --------------------------------------------------------------------------
def test_a_rejected_artefact_reached_by_the_template_map_is_dropped():
    """P7 itself: T09 maps to Art.13, exists, and was sent back for rerun."""
    assert _supporting_tids(_state(), "Art.13") == ["T02_system_card"]


def test_a_rejected_artefact_reachable_only_by_citation_stays_dropped():
    """Regression guard on the branch that was already right.

    ``T10`` has no ``_TEMPLATE_ARTICLES`` row, so the citation branch is the
    only one that could have reached it — and that branch always filtered.
    """
    assert "T10_explainability_report" not in _supporting_tids(_state(), "Art.13")


def test_the_template_map_drops_a_rejected_artefact_for_every_article():
    """P7 named Art.13; the same branch put a rejected T11 under Art.15."""
    assert _supporting_tids(_state(), "Art.15") == []


def test_an_admitted_artefact_survives_both_branches_in_order():
    """Citations first, then the template map — the order T17 has always printed."""
    state = _state()
    state["verifier_critiques"]["T04_risk_tier_decision"] = {
        "verdict": "accept", "article_citations": ["Art.5"]}
    state["phase_artefacts"]["T04_risk_tier_decision"] = {"uri": "minio://e/p/T04.json"}
    assert _supporting_tids(state, "Art.5") == ["T02_system_card", "T04_risk_tier_decision"]


def test_the_candidates_are_the_union_of_both_partitions():
    """Every candidate is either cited or excluded — the split loses nothing."""
    state = _state()
    cited = _supporting_tids(state, "Art.13")
    excluded = [tid for tid, _ in _excluded_tids(state, "Art.13")]
    assert sorted(cited + excluded) == sorted(_candidate_tids(state, "Art.13"))


def test_the_evidence_uris_carry_only_admitted_artefacts():
    """The T17 field says 'URIs of admitted phase artefacts'; now it holds them."""
    entry = _evidence_entry(_state(), "Art.13", "PASS", [])
    assert entry["evidence_uris"] == ["minio://e/p/T02_system_card.json"]


# --------------------------------------------------------------------------
# what is said about the artefacts that were dropped
# --------------------------------------------------------------------------
def test_the_excluded_artefacts_are_named_with_the_verdict_that_barred_them():
    """Including T10, which no template row maps to and only its citation reaches."""
    assert _excluded_tids(_state(), "Art.13") == [
        ("T09_model_card", "rerun"), ("T10_explainability_report", "rerun")]


def test_an_uncritiqued_candidate_is_labelled_as_such_not_as_rejected():
    """'not critiqued' and 'rerun' are different findings about an artefact."""
    state = _state()
    del state["verifier_critiques"]["T09_model_card"]
    assert ("T09_model_card", "not critiqued") in _excluded_tids(state, "Art.13")


def test_the_rationale_names_the_admitted_evidence_and_the_excluded():
    """P7's own sentence, corrected: T02 admitted, T09 named as excluded."""
    rationale = _evidence_entry(_state(), "Art.13", "PASS", [])["rationale"]
    assert "verifier-accepted evidence (T02_system_card)" in rationale
    assert "T09_model_card (rerun)" in rationale


def test_a_fail_rationale_also_records_what_it_may_not_cite():
    """The exclusion is traceability, so it does not depend on the verdict."""
    findings = [{"description": "d", "finding_id": "F1"}]
    rationale = _evidence_entry(_state(), "Art.10", "FAIL", findings)["rationale"]
    assert "T06_datasheet_for_datasets (escalate_hitl)" in rationale


def test_a_fully_admitted_article_says_nothing_about_exclusions():
    """Silence on the healthy path — the note appears only when something was barred."""
    state = _state()
    for tid in ("T09_model_card", "T10_explainability_report"):
        state["verifier_critiques"][tid]["verdict"] = "accept"
    assert "excluded" not in _evidence_entry(state, "Art.13", "PASS", [])["rationale"]
    assert _exclusion_note([]) == ""


def test_a_pass_on_no_admitted_artefact_does_not_claim_one():
    """The old ``or 'phase artefacts'`` fallback asserted admission while naming none."""
    rationale = _rationale("PASS", [], [])
    assert "phase artefacts" not in rationale
    assert "no verifier-accepted artefact" in rationale


def test_observations_on_no_admitted_artefact_do_not_claim_one_either():
    """The same fallback stood in the PASS_WITH_OBSERVATIONS branch."""
    rationale = _rationale("PASS_WITH_OBSERVATIONS", [], [{"description": "d"}])
    assert "phase artefacts" not in rationale
    assert "no verifier-accepted artefact" in rationale


# --------------------------------------------------------------------------
# the admission rule the citation rule now shares
# --------------------------------------------------------------------------
def test_the_intake_artefacts_still_admit_their_articles():
    """Regression guard: folding the second rule in must not lose Art.11/Annex_IV."""
    assert {"Art.11", "Annex_IV"} <= _collect_admitted_articles(_state())


def test_a_rejected_intake_dossier_admits_no_articles():
    """The one behaviour the fold changes; nothing critiques Stage B today."""
    state = _state()
    state["verifier_critiques"]["T01b_annex_iv_dossier"] = {"verdict": "rerun"}
    del state["phase_artefacts"]["T01c_intake_completeness_report"]
    assert "Art.11" not in _collect_admitted_articles(state)


def test_a_rejected_artefact_admits_nothing_it_cites():
    """Regression guard on the half that was already right."""
    assert "Art.15" not in _collect_admitted_articles(_state())


def test_the_verdict_is_untouched_when_only_the_basis_narrows():
    """P7: 'The verdict is sound (admission came from T02); the stated basis is not.'"""
    state = _state()
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.13"] == "PASS"
    assert state["article_evidence"]["Art.13"]["supporting_template_ids"] == [
        "T02_system_card"]


def test_the_hitl_packet_inherits_the_filter():
    """The reviewer's evidence comes from article_evidence, so it narrows with it.

    The escalated T06 also cites Art. 13, so its review packet gathers that
    article's evidence — which held the rejected T09 before this fix.
    """
    state = _state(hitl_required=True, phase_status={t: "M" for t in _ARTEFACTS},
                   client_submission={"stage_a": {"provider_name": "A", "system_name": "X"}})
    state["verifier_critiques"]["T06_datasheet_for_datasets"]["article_citations"] = [
        "Art.10", "Art.13"]
    _derive_verdicts(state)
    case = next(c for c in build_hitl_review_packet(state)["cases"]
                if c["template_id"] == "T06_datasheet_for_datasets")
    assert any("T02_system_card" in uri for uri in case["evidence_uris"])
    assert not any("T09_model_card" in uri for uri in case["evidence_uris"])
