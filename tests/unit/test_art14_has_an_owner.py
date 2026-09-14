"""Fix 31 (Q1) — Art. 14 has an accountable artefact, so a gate can hold it.

Art. 14 (human oversight) was absent from the delivered compliance matrix and
absent from part 1's run before it, unnoticed because 15 rows looked complete.
The cause was not a gate that missed it: no template in `_TEMPLATE_ARTICLES`
mapped to Art. 14 at all, so no phase was accountable for human oversight and no
gate could hold an article nothing had claimed.

The evidence was in the engagement the whole time. The client's own CGSA payload
carries `eu_ai_act_compliance_matrix.article_14` → domain D5, *Human Oversight
and Accountability*, control C26 — and D5 arrives inside T14_governance_findings
beside D1 (Art. 9) and D6 (Art. 17). Only the route from that artefact to that
article was missing.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix import _TEMPLATE_ARTICLES
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.verification.unadmitted import gate_on_unadmitted
from aaa.agents.tier2.report_architect.constants import ARTICLE_PHASE
from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET
from aaa.tools.regulatory_coverage.unowned import KNOWN_UNOWNED

T14 = "T14_governance_findings"
P5_ARTICLES = {T14: ["Art.9", "Art.14", "Art.17"],
               "T15_monitoring_logging_review": ["Art.12", "Art.72"]}


def _state(verdict: str) -> dict:
    return {
        "verifier_critiques": {T14: {"verdict": verdict,
                                     "article_citations": ["Art.9", "Art.17"]}},
        "phase_artefacts": {T14: {"uri": "minio://x/T14"}},
        "blocking_findings": [], "compliance_matrix": {}, "scope_gate": {},
        "insufficient_evidence_articles": [],
    }


def test_every_in_scope_article_now_has_an_accountable_template():
    """Fix 31's guard, kept for the tier it was written against.

    Fix 41 generalised it — every tier, and schedulability as well as ownership,
    in ``test_article_ownership_every_tier.py``. The declared-gap list lives there
    too, as ``ownership.KNOWN_UNOWNED``, so there is one list of this fact rather
    than two that can disagree.
    """
    owned = {article for articles in _TEMPLATE_ARTICLES.values() for article in articles}
    unowned = set(ARTICLE_SET["high"]) - owned

    assert unowned == set(KNOWN_UNOWNED) & set(ARTICLE_SET["high"])


def test_the_art50_gap_is_a_missing_owner_and_not_a_mis_attributed_one():
    """Fix 47: whatever comes to own Art. 50, it is not a fairness artefact."""
    for tid in ("T12_output_fairness_report", "T13_output_sampling_log"):
        assert "Art.50" not in _TEMPLATE_ARTICLES.get(tid, [])


def test_art14_is_owned_by_the_artefact_that_carries_its_evidence():
    assert "Art.14" in _TEMPLATE_ARTICLES[T14]
    assert ARTICLE_PHASE["Art.14"] == "P5"


def test_the_phase_that_emits_t14_is_accountable_for_art14():
    """The runner's contract and the template map have to agree, or the gate misses."""
    from aaa.agents.tier1.phases.phase_runners.phase import p5 as phase_5

    source = phase_5.__file__
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    assert '"T14_governance_findings": ["Art.9", "Art.14", "Art.17"]' in text


def test_an_admitted_t14_evidences_human_oversight():
    state = _state("accept")

    _derive_verdicts(state)

    assert state["compliance_matrix"]["Art.14"] == "PASS"
    assert T14 in state["article_evidence"]["Art.14"]["supporting_template_ids"]


def test_an_escalated_t14_takes_art14_with_it_rather_than_dropping_it():
    """Fix 26's gate can only hold an article some artefact claimed (Q1)."""
    state = _state("escalate_hitl")

    newly = gate_on_unadmitted(state, P5_ARTICLES, phase_id="P5", phase_label="Phase 5")
    _derive_verdicts(state)

    assert "Art.14" in newly
    assert state["compliance_matrix"]["Art.14"] == "INSUFFICIENT_EVIDENCE"


def test_art14_is_a_core_high_risk_article_and_still_drives_a_disclaimer():
    from aaa.agents.tier1.phases.compliance_matrix.compute_final_verdict import (
        _compute_final_verdict,
    )

    state = {"compliance_matrix": {"Art.14": "INSUFFICIENT_EVIDENCE"},
             "intake_completeness_score": 1.0, "completeness_score": 1.0,
             "regulatory_coverage_pct": 100.0}

    assert _compute_final_verdict(state) == "DISCLAIMER_OF_OPINION"
    assert state["opinion_disclaimer"] is True


def test_the_cgsa_payload_supplies_the_controls_for_the_article():
    """`_cgsa_controls_for` already resolved Art. 14 → C26; nothing asked it to."""
    from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import _cgsa_controls_for

    state = {"cgsa_payload": {"eu_ai_act_compliance_matrix": {
        "article_14": {"article_title": "Human oversight", "controls_mapped": ["C26"]}}}}

    assert _cgsa_controls_for(state, "Art.14") == ["C26"]
