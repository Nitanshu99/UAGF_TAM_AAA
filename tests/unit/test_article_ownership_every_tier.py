"""Fix 41 — every tier, every article: is it owned, and will its owner run? (R9)

Fix 31 added a guard asserting that every article in ``ARTICLE_SET["high"]`` has
an accountable template. It checked **one tier** and asked **one question**, and
so it could not see RetailIQ: in scope `{Art.13, Art.50, Annex_IV}`, and Art. 50 —
the only substantive transparency obligation a limited-risk system carries — was
assessed by nothing and did not appear in the delivered table at all.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix import _TEMPLATE_ARTICLES
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.compliance_matrix.unassessable import (
    UNASSESSABLE_FINDING_ID,
    record_unassessable,
    scope_seed,
)
from aaa.tools.csp_solver import solve_phase_plan
from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET
from aaa.tools.regulatory_coverage.engagement_scope import engagement_articles
from aaa.tools.regulatory_coverage.ownership import TEMPLATE_PHASE, article_owners, is_schedulable
from aaa.tools.regulatory_coverage.unowned import KNOWN_UNOWNED

#: A representative engagement per tier, enough for the planner to solve.
TIERS: dict[str, tuple[str, str, bool]] = {
    "high": ("high", "tabular", False),
    "high_llm": ("high", "llm", True),
    "limited": ("limited", "time_series", False),
    "minimal": ("minimal", "tabular", False),
    "gpai": ("gpai", "gpai", True),
}


def _plan(tier: str) -> dict[str, str]:
    risk, modality, is_llm = TIERS[tier]
    return solve_phase_plan({"risk_tier": risk, "modality": modality,
                             "is_llm_or_agentic": is_llm, "annex_iii_mapping": [],
                             "special_category_data": False})


# --------------------------------------------------------------------------- #
# every tier is covered, and a failure names the tier and the article
# --------------------------------------------------------------------------- #

def test_the_guard_covers_every_tier_the_article_set_declares():
    assert set(TIERS) == set(ARTICLE_SET) - {"prohibited"}, (
        "a tier in ARTICLE_SET that this guard does not exercise is a tier whose "
        "articles nobody has checked for an owner")


@pytest.mark.parametrize("tier", sorted(TIERS))
def test_every_in_scope_article_is_owned_or_declared_unowned(tier):
    unowned = sorted(a for a in ARTICLE_SET[tier]
                     if not article_owners(a, _TEMPLATE_ARTICLES))
    undeclared = [a for a in unowned if a not in KNOWN_UNOWNED]
    assert not undeclared, (
        f"tier '{tier}': {', '.join(undeclared)} bind this engagement and no "
        f"template evidences them. Either give them an artefact that carries the "
        f"evidence, or declare them in ownership.KNOWN_UNOWNED with the reason.")


@pytest.mark.parametrize("tier", sorted(TIERS))
def test_every_owned_in_scope_article_has_a_scheduled_owner(tier):
    plan = _plan(tier)
    unscheduled = sorted(
        f"{a} (owners {sorted(article_owners(a, _TEMPLATE_ARTICLES))}, "
        f"plan {({p: plan.get(p) for p in sorted(article_owners(a, _TEMPLATE_ARTICLES))})})"
        for a in ARTICLE_SET[tier]
        if article_owners(a, _TEMPLATE_ARTICLES)
        and not is_schedulable(a, plan, _TEMPLATE_ARTICLES))
    assert not unscheduled, (
        f"tier '{tier}': these articles have an owner the planner will not run — "
        + "; ".join(unscheduled))


def test_the_declared_gaps_are_exactly_the_real_ones():
    """A hole that closes must leave the list, or the list stops meaning anything."""
    real = {a for tier in TIERS for a in ARTICLE_SET[tier]
            if not article_owners(a, _TEMPLATE_ARTICLES)}
    # Reach scope via a Stage A flag, not a tier. Art. 50 joined them in fix 51:
    # it is conditional on the system type and was wrongly in all five tier sets.
    gate_only = {"Art.25", "Art.27", "Art.50"}
    assert set(KNOWN_UNOWNED) - gate_only == real


def test_every_declared_gap_gives_a_reason():
    for article, why in KNOWN_UNOWNED.items():
        assert len(why) > 20, f"{article} is exempted without a reason"


# --------------------------------------------------------------------------- #
# the owner set, not a single phase
# --------------------------------------------------------------------------- #

def test_art_15_survives_a_plan_that_skips_phase_3():
    """`ARTICLE_PHASE` says Art.15 is P3's; an LLM engagement skips P3 outright."""
    plan = _plan("high_llm")
    assert plan["P3"] == "S"
    assert "CYBER" in article_owners("Art.15", _TEMPLATE_ARTICLES)
    assert is_schedulable("Art.15", plan, _TEMPLATE_ARTICLES)


def test_an_article_owned_only_by_a_skipped_phase_is_not_schedulable():
    assert not is_schedulable("Art.10", {"P2": "S"}, {"T06_datasheet_for_datasets": ["Art.10"]})


def test_intake_and_phase_6_always_run():
    assert is_schedulable("Annex_IV", {}, {"T01b_annex_iv_dossier": ["Annex_IV"]})


def test_every_template_the_matrix_maps_has_a_phase():
    missing = sorted(set(_TEMPLATE_ARTICLES) - set(TEMPLATE_PHASE))
    assert not missing, f"templates with no emitting phase: {missing}"


# --------------------------------------------------------------------------- #
# the runtime consequence: listed, not omitted
# --------------------------------------------------------------------------- #

def _limited(**kw) -> dict:
    """A limited-tier engagement whose Stage A gate raised Art. 50.

    Since fix 51 that flag is the *only* way Art. 50 enters an engagement — it is
    conditional on the system interacting with natural persons, and no longer sits
    in every tier set. It is still the article no artefact evidences, so it is
    still what an unassessable in-scope article looks like.
    """
    kw.setdefault("scope_gate", {"triggers_art50_transparency": True})
    return {"engagement_id": "eng-02", "risk_tier": "limited",
            "declared_risk_tier": "limited", "is_llm_or_agentic": False,
            "phase_artefacts": {}, "verifier_critiques": {}, **kw}


def test_an_in_scope_article_nothing_evidenced_is_listed_not_absent():
    """RetailIQ's Art. 50 was in KPI 2's denominator and in no row of the table."""
    state = _limited()
    _derive_verdicts(state)
    assert set(state["compliance_matrix"]) == engagement_articles(state)
    assert state["compliance_matrix"]["Art.50"] == "INSUFFICIENT_EVIDENCE"


def test_the_finding_says_the_reason_is_structural():
    state = _limited()
    _derive_verdicts(state)
    finding = next(f for f in state["blocking_findings"]
                   if f["finding_id"] == UNASSESSABLE_FINDING_ID)
    assert finding["eu_ai_act_articles"] == ["Art.50"]
    assert "re-running the audit will not change them" in finding["description"]
    assert "no artefact in the catalogue" in finding["description"] or \
        "disclosure evidence" in finding["description"]


def test_an_unknown_tier_seeds_nothing():
    """The same reading fix 40 gives an unstated scope: invent nothing."""
    assert scope_seed({"phase_artefacts": {}}) == set()


def test_an_article_already_present_under_an_alias_is_not_seeded_again():
    """Case 04 carries Art.51-Art.55 where ARTICLE_SET says GPAI_51-GPAI_55."""
    state = {"risk_tier": "high", "declared_risk_tier": "high", "is_llm_or_agentic": True}
    seeded = scope_seed(state, {f"Art.{n}" for n in range(51, 56)})
    assert not {f"GPAI_{n}" for n in range(51, 56)} & seeded


def test_a_second_derivation_does_not_stack_the_finding():
    state = _limited()
    _derive_verdicts(state)
    _derive_verdicts(state)
    assert len([f for f in state["blocking_findings"]
                if f["finding_id"] == UNASSESSABLE_FINDING_ID]) == 1


def test_an_article_something_evidenced_is_not_reported_unassessable():
    state = _limited(verifier_critiques={"T02_system_card": {"verdict": "accept"}},
                     phase_artefacts={"T02_system_card": {"uri": "minio://x/T02"}})
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.13"] == "PASS"
    finding = next(f for f in state["blocking_findings"]
                   if f["finding_id"] == UNASSESSABLE_FINDING_ID)
    assert "Art.13" not in finding["eu_ai_act_articles"]


def test_record_unassessable_is_a_no_op_when_everything_is_assessable():
    state = {"risk_tier": "minimal", "declared_risk_tier": "minimal"}
    assert record_unassessable(state, {"Art.50": "PASS"}) == []
    assert not state.get("blocking_findings")
