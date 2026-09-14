"""Fix 40 — a phase→article claim is intersected with the engagement's scope (R8).

RetailIQ is `limited`: in scope `{Art.13, Annex_IV}` — and `{Art.13, Art.50,
Annex_IV}` when this was written, before fix 51 established that Art. 50 is the
Stage A gate's to raise and not every tier's to assume. It was delivered a
conformity table of thirteen articles, eleven of which do not bind it — Art. 11
reported **PASS**, the other ten `INSUFFICIENT_EVIDENCE`. The Verifier caught it
unaided and graded it `material` (case 02 #023).
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.verification.confidence import gate_on_confidence
from aaa.agents.tier1.phases.verification.no_report import gate_on_no_report
from aaa.agents.tier1.phases.verification.unadmitted import gate_on_unadmitted
from aaa.tools.regulatory_coverage import covered_articles
from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET
from aaa.tools.regulatory_coverage.engagement_scope import (
    core_article,
    engagement_articles,
    is_in_scope,
    keep_in_scope,
    scope_is_known,
)

#: What the GovernanceAgent's tier-agnostic contract claims, whatever the client is.
P5_TIDS = {"T14_governance_findings": ["Art.9", "Art.14", "Art.17"],
           "T15_monitoring_logging_review": ["Art.12", "Art.72"]}


def _state(tier: str = "limited", **kw) -> dict:
    return {"engagement_id": "eng-02", "risk_tier": tier, "declared_risk_tier": tier,
            "is_llm_or_agentic": kw.pop("is_llm", False),
            "phase_artefacts": {}, "verifier_critiques": {}, **kw}


# --------------------------------------------------------------------------- #
# one authority, per tier
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("tier", sorted(ARTICLE_SET))
def test_every_tier_resolves_to_its_own_set(tier):
    assert engagement_articles(_state(tier)) >= ARTICLE_SET[tier]


def test_a_high_risk_llm_engagement_gets_the_gpai_articles_too():
    scope = engagement_articles(_state("high", is_llm=True))
    assert "GPAI_53" in scope and "Art.9" in scope


def test_a_limited_engagement_carries_two_articles():
    """Art. 50 left every tier set in fix 51 — it is conditional, and gated."""
    assert engagement_articles(_state("limited")) == {"Art.13", "Annex_IV"}


def test_a_minimal_engagement_carries_none():
    """A minimal-risk system has no mandatory requirements under the Act."""
    assert engagement_articles(_state("minimal")) == set()


def test_art_50_reaches_an_engagement_only_through_the_gate():
    """Finding R18: it used to be in all five tier sets as well."""
    for tier in ("high", "high_llm", "limited", "minimal", "gpai"):
        assert "Art.50" not in engagement_articles(_state(tier))
    gated = _state("high", scope_gate={"triggers_art50_transparency": True})
    assert "Art.50" in engagement_articles(gated)


def test_the_scope_gate_widens_the_tiers_set():
    """Art. 27 is in no ARTICLE_SET — it reaches an engagement only via a flag."""
    state = _state("high", scope_gate={"triggers_fria": True})
    assert "Art.27" in engagement_articles(state)
    assert "Art.27" not in ARTICLE_SET["high"]


# --------------------------------------------------------------------------- #
# scope binds at the article, not the sub-article
# --------------------------------------------------------------------------- #

def test_a_sub_article_is_in_scope_when_its_parent_is():
    assert core_article("Art.15§1") == "Art.15"
    assert is_in_scope(_state("high"), "Art.15§1")
    assert is_in_scope(_state("high"), "Art.10§2(f)")


def test_a_sub_article_of_an_out_of_scope_article_is_out():
    assert not is_in_scope(_state("limited"), "Art.15§1")


# --------------------------------------------------------------------------- #
# an unstated tier is not a narrow one
# --------------------------------------------------------------------------- #

def test_an_unstated_tier_does_not_narrow_anything():
    """Phase 1 establishes the tier, and R1 lost Phase 1 in four of five cases."""
    state = {"phase_artefacts": {}}
    assert scope_is_known(state) is False
    assert keep_in_scope(state, ["Art.9", "Art.10"]) == ["Art.9", "Art.10"]
    assert "out_of_scope_claims" not in state


def test_a_declared_tier_is_enough_to_filter_on():
    state = {"declared_risk_tier": "limited"}
    assert scope_is_known(state) is True
    assert keep_in_scope(state, ["Art.9", "Art.13"]) == ["Art.13"]


def test_an_unrecognised_tier_does_not_narrow_anything():
    assert scope_is_known({"risk_tier": "not_a_tier"}) is False


# --------------------------------------------------------------------------- #
# what is dropped is recorded, not silent
# --------------------------------------------------------------------------- #

def test_a_dropped_article_is_recorded_with_its_claimant():
    state = _state("limited")
    assert keep_in_scope(state, ["Art.9", "Art.13"], claimed_by="Phase 5") == ["Art.13"]
    assert state["out_of_scope_claims"] == [
        {"article": "Art.9", "claimed_by": "Phase 5", "risk_tier": "limited"}]


def test_the_same_claim_is_not_recorded_twice():
    state = _state("limited")
    keep_in_scope(state, ["Art.9"], claimed_by="Phase 5")
    keep_in_scope(state, ["Art.9"], claimed_by="Phase 5")
    assert len(state["out_of_scope_claims"]) == 1


def test_no_finding_is_raised_because_nothing_is_wrong_with_the_client():
    state = _state("limited")
    keep_in_scope(state, ["Art.9"], claimed_by="Phase 5")
    assert "blocking_findings" not in state


# --------------------------------------------------------------------------- #
# the gates, whose inputs are the tier-agnostic contracts
# --------------------------------------------------------------------------- #

def test_an_unadmitted_artefact_holds_back_only_what_binds():
    state = _state("limited", verifier_critiques={
        "T14_governance_findings": {"verdict": "escalate_hitl"}})
    assert gate_on_unadmitted(state, {"T14_governance_findings": ["Art.9", "Art.13"]},
                              phase_id="P5", phase_label="Phase 5") == ["Art.13"]
    assert state["insufficient_evidence_articles"] == ["Art.13"]


def test_a_lost_phase_holds_back_only_what_binds():
    state = _state("limited")
    assert gate_on_no_report(state, P5_TIDS, phase_id="P5",
                             phase_label="Phase 5") == []
    assert state["insufficient_evidence_articles"] == []


def test_a_low_confidence_phase_holds_back_only_what_binds():
    state = _state("limited")
    assert gate_on_confidence(state, {"T09_model_card": ["Art.13", "Art.15"]}, 0.1,
                              phase_id="P3", phase_label="Phase 3") == ["Art.13"]


# --------------------------------------------------------------------------- #
# nothing out of scope reaches the matrix, and KPI 2 agrees with it
# --------------------------------------------------------------------------- #

def test_no_out_of_scope_article_reaches_the_matrix():
    """Fix 41 made the matrix the in-scope set exactly — no more, and no less."""
    state = _state("limited", insufficient_evidence_articles=[
        "Art.5", "Art.9", "Art.13", "Art.72"])
    _derive_verdicts(state)
    assert set(state["compliance_matrix"]) == engagement_articles(state)
    assert not {"Art.5", "Art.9", "Art.72"} & set(state["compliance_matrix"])


def test_a_high_risk_engagement_keeps_every_article_it_had():
    """Acceptance: no in-scope article may leave. Fix 41 may add absent ones."""
    articles = ["Art.5", "Art.9", "Art.13", "Art.72", "Art.15§1", "Art.10§2(f)"]
    state = _state("high", insufficient_evidence_articles=list(articles))
    _derive_verdicts(state)
    matrix = set(state["compliance_matrix"])
    assert set(articles) <= matrix
    assert all(is_in_scope(state, a) for a in matrix)


def test_kpi_2_and_the_matrix_cannot_describe_different_audits():
    state = _state("high", scope_gate={"triggers_fria": True},
                   insufficient_evidence_articles=["Art.27"])
    _derive_verdicts(state)
    kpi = covered_articles(state)
    assert "Art.27" in state["compliance_matrix"]
    assert "Art.27" in kpi["in_scope"]


# --------------------------------------------------------------------------- #
# one obligation, two spellings (finding R17 — resolved for the scope test only)
# --------------------------------------------------------------------------- #

def test_the_l_branchs_gpai_spelling_is_in_scope_for_a_high_risk_llm():
    """Case 04's five PASS rows are `Art.51`-`Art.55`; the set says `GPAI_51`-`55`."""
    from aaa.tools.regulatory_coverage.engagement_scope import canonical_article

    state = _state("high", is_llm=True)
    assert canonical_article("Art.53") == "GPAI_53"
    for n in range(51, 56):
        assert is_in_scope(state, f"Art.{n}")
        assert is_in_scope(state, f"GPAI_{n}")


def test_the_alias_does_not_rewrite_the_delivered_id():
    """Rewriting it would move case 04's coverage inside a fix that must not."""
    state = _state("high", is_llm=True)
    assert keep_in_scope(state, ["Art.51", "GPAI_52"]) == ["Art.51", "GPAI_52"]


def test_the_gpai_articles_still_do_not_bind_a_limited_engagement():
    assert not is_in_scope(_state("limited"), "Art.51")


def test_the_alias_is_not_applied_to_an_unrelated_article():
    from aaa.tools.regulatory_coverage.engagement_scope import canonical_article
    assert canonical_article("Art.5") == "Art.5"
    assert canonical_article("Art.50") == "Art.50"
    assert canonical_article("Art.15") == "Art.15"


# --------------------------------------------------------------------------- #
# fix 51 (R18) — an empty scope says which kind of empty it is
# --------------------------------------------------------------------------- #

def test_a_minimal_engagement_reports_no_obligations_rather_than_full_coverage():
    """100 % over nothing is true, and it must not read as 'everything assessed'."""
    from aaa.tools.regulatory_coverage import covered_articles

    kpi = covered_articles(_state("minimal"))
    assert kpi["in_scope"] == []
    assert kpi["no_obligations_in_scope"] is True
    assert kpi["regulatory_coverage_pct"] == 100.0


def test_an_engagement_with_no_stated_tier_does_not_pass_by_having_no_scope():
    """The other kind of empty: nobody worked out what binds it.

    Before fix 51 this was unreachable, because `minimal` still held Art. 50 and
    an unknown tier resolved to it. With the set empty, reporting 100 % would let
    an unscoped engagement pass by having no obligations to fail.
    """
    from aaa.tools.regulatory_coverage import covered_articles

    kpi = covered_articles({"phase_artefacts": {}, "verifier_critiques": {},
                            "compliance_matrix": {}})
    assert kpi["in_scope"] == []
    assert kpi["no_obligations_in_scope"] is False
    assert kpi["regulatory_coverage_pct"] == 0.0


def test_the_gated_article_is_still_reported_when_the_flag_is_set():
    """Art. 50 applying and being unevidenced is a real finding, not an omission."""
    from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts

    state = _state("high", scope_gate={"triggers_art50_transparency": True})
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.50"] == "INSUFFICIENT_EVIDENCE"
    assert any(f["finding_id"] == "ORCH-ARTICLE-UNASSESSABLE"
               for f in state["blocking_findings"])
