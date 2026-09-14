"""Fixes 24 and 25 — a scope-gate flag says an obligation applies, not that it is met.

Fix 24 stops the four Stage A scope-gate flags admitting their articles as
*evidence*.  Fix 25 is what makes that safe: the KPI floor sat below the
qualified-pass branch, so admitting an article was unassessable used to return
before the floor was consulted, and the more honest audit came out with the
better verdict.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.compute_final_verdict import _compute_final_verdict
from aaa.agents.tier1.phases.compliance_matrix.scope_articles import (
    SCOPE_FINDING_ID,
    scope_gate_articles,
)
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION, FAIL, PASS, PASS_WITH_OBSERVATIONS
from tests.unit.support.real_auditor_state import base_state

_GPAI = ["GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55"]


def _gated(flag: str, **over: object) -> dict:
    """A completed high-risk state with one scope-gate flag set."""
    state = base_state(scope_gate={flag: True}, risk_tier="high",
                       is_llm_or_agentic=True, **over)
    node_compliance_matrix(state)
    return state


def _ladder(**over: object) -> dict:
    """A state whose KPIs and matrix are set directly, for the verdict ladder."""
    state = {"compliance_matrix": {"Art.10": "PASS"}, "intake_completeness_score": 1.0,
             "completeness_score": 1.0, "regulatory_coverage_pct": 100.0,
             "cgsa_phase5_verdict": "PASS", "cgsa_csp_satisfiable": True}
    state.update(over)
    return state


# --------------------------------------------------------------------------
# fix 24 — the flag brings an article into scope, and evidences nothing
# --------------------------------------------------------------------------
@pytest.mark.parametrize("flag, articles", [
    ("become_provider_under_art25", ["Art.25"]),
    ("triggers_fria", ["Art.27"]),
    ("triggers_art50_transparency", ["Art.50"]),
    ("is_gpai_systemic", _GPAI),
])
def test_a_flag_alone_cannot_pass_an_article(flag, articles):
    """Each of the four used to answer PASS on zero evidence."""
    matrix = _gated(flag)["compliance_matrix"]

    assert [matrix[a] for a in articles] == ["INSUFFICIENT_EVIDENCE"] * len(articles)


@pytest.mark.parametrize("flag, articles", [
    ("triggers_fria", ["Art.27"]),
    ("is_gpai_systemic", _GPAI),
])
def test_the_article_still_reaches_the_matrix(flag, articles):
    """Dropping it from `admitted` alone would delete it — and its coverage row."""
    assert set(articles) <= set(_gated(flag)["compliance_matrix"])


def test_the_gpai_articles_use_the_spelling_the_rest_of_the_system_uses():
    """``Arts.51-55`` matched no ARTICLE_SET, template map or phase mapping."""
    matrix = _gated("is_gpai_systemic")["compliance_matrix"]

    assert "Arts.51-55" not in matrix
    assert set(_GPAI) <= set(matrix)


def test_the_gate_admits_no_article_by_itself():
    """The admission set is now purely artefact-derived."""
    admitted = _collect_admitted_articles(
        {"scope_gate": {f: True for f in
                        ("become_provider_under_art25", "triggers_fria",
                         "triggers_art50_transparency", "is_gpai_systemic")},
         "verifier_critiques": {}, "phase_artefacts": {}})

    assert admitted == set()


def test_an_evidenced_gate_article_still_passes():
    """The gate does not downgrade — it just stops being an upgrade.

    The fixture used to evidence Art. 50 with a `T13_output_sampling_log` citing
    it, which fix 47 established is a mis-attribution and fix 50 now refuses: an
    output sampling log examines outputs for bias and evidences nothing about
    disclosure. **No artefact evidences Art. 50** (finding R18), so the subject
    of this test is demonstrated on the one gate flag whose articles *are*
    evidenceable — `is_gpai_systemic`, whose GPAI ids the L-branch owns (fix 49).
    """
    state = base_state(risk_tier="high", declared_risk_tier="high",
                       is_llm_or_agentic=True,
                       scope_gate={"is_gpai_systemic": True})
    state["verifier_critiques"]["T16_uagf_tam_l_evidence"] = {
        "verdict": "accept", "article_citations": ["GPAI_51"]}
    state["phase_artefacts"]["T16_uagf_tam_l_evidence"] = {"uri": "minio://x/T16"}
    node_compliance_matrix(state)

    assert state["compliance_matrix"]["GPAI_51"] == PASS
    assert "GPAI_51" not in [a for f in state["blocking_findings"]
                             if f["finding_id"] == SCOPE_FINDING_ID
                             for a in f["eu_ai_act_articles"]]


def test_a_gate_article_no_artefact_evidences_cannot_pass(caplog):
    """Finding R18, asserted rather than discovered again.

    Three of the four scope-gate flags raise articles no template owns — Art. 25,
    Art. 27 and Art. 50 — so the gate can only ever put them in the matrix as
    unevidenced. That is correct behaviour on a real gap, and the gap is real.
    """
    from aaa.agents.tier1.phases.compliance_matrix import _TEMPLATE_ARTICLES
    from aaa.tools.regulatory_coverage.ownership import article_owners

    for article in ("Art.25", "Art.27", "Art.50"):
        assert not article_owners(article, _TEMPLATE_ARTICLES)

    state = base_state(scope_gate={"triggers_art50_transparency": True})
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.50"] == "INSUFFICIENT_EVIDENCE"


def test_the_rationale_says_where_the_article_came_from():
    """A reader meets Art.27 with no phase and no artefact behind it."""
    rationale = _gated("triggers_fria")["article_evidence"]["Art.27"]["rationale"]

    assert "triggers_fria" in rationale
    assert "not that it is met" in rationale


def test_the_unevidenced_articles_are_recorded_and_reported_once():
    """One aggregate finding, and the articles land in the insufficiency list."""
    state = _gated("is_gpai_systemic")
    findings = [f for f in state["blocking_findings"] if f["finding_id"] == SCOPE_FINDING_ID]

    assert len(findings) == 1
    assert findings[0]["materiality"] == "possibly_material"
    assert findings[0]["eu_ai_act_articles"] == _GPAI
    assert set(_GPAI) <= set(state["insufficient_evidence_articles"])


def test_a_second_pass_changes_nothing():
    """The finding is ``possibly_material``; without the insufficiency record a
    re-derivation would read it as a qualification and answer PASS_WITH_OBSERVATIONS."""
    state = _gated("triggers_fria")
    matrix, verdict = dict(state["compliance_matrix"]), state["final_verdict"]
    node_compliance_matrix(state)

    assert state["compliance_matrix"] == matrix
    assert state["final_verdict"] == verdict
    assert sum(1 for f in state["blocking_findings"]
               if f["finding_id"] == SCOPE_FINDING_ID) == 1


def test_an_engagement_with_no_flags_says_nothing_about_scope():
    """Silence on the healthy path."""
    state = base_state(risk_tier="high")
    node_compliance_matrix(state)

    assert not [f for f in state["blocking_findings"] if f["finding_id"] == SCOPE_FINDING_ID]
    assert "scope gate" not in state["article_evidence"]["Art.10"]["rationale"]


def test_the_mapping_names_the_flag_behind_each_article():
    """Every article carries the flag that put it in scope."""
    gate = {"triggers_fria": True, "is_gpai_systemic": True}

    assert scope_gate_articles({"scope_gate": gate}) == {
        "Art.27": "triggers_fria", **{a: "is_gpai_systemic" for a in _GPAI}}


# --------------------------------------------------------------------------
# fix 25 — the KPI floor is not skippable
# --------------------------------------------------------------------------
def test_the_same_coverage_cannot_give_the_more_honest_audit_the_better_verdict():
    """The anomaly itself: 25% coverage either way, one article's honesty apart."""
    honest = _ladder(compliance_matrix={"Art.10": "PASS", "Art.50": "INSUFFICIENT_EVIDENCE"},
                     regulatory_coverage_pct=25.0)
    silent = _ladder(compliance_matrix={"Art.10": "PASS"}, regulatory_coverage_pct=25.0)

    assert _compute_final_verdict(honest) == _compute_final_verdict(silent)
    assert _compute_final_verdict(honest) == DISCLAIMER_OF_OPINION


def test_below_the_floor_a_non_core_gap_disclaims():
    """It returned PASS_WITH_OBSERVATIONS: the floor was below the branch that fired."""
    state = _ladder(compliance_matrix={"Art.43": "INSUFFICIENT_EVIDENCE"},
                    regulatory_coverage_pct=0.0)

    assert _compute_final_verdict(state) == DISCLAIMER_OF_OPINION
    assert state["opinion_disclaimer"] is True


def test_above_the_floor_a_non_core_gap_is_still_a_qualified_pass():
    """Fix 25 moves the floor, not the core-article predicate."""
    state = _ladder(compliance_matrix={"Art.10": "PASS", "Art.43": "INSUFFICIENT_EVIDENCE"})

    assert _compute_final_verdict(state) == PASS_WITH_OBSERVATIONS
    assert state["opinion_disclaimer"] is False


def test_a_core_gap_disclaims_even_with_every_kpi_met():
    """Regression guard on the predicate F11 established."""
    state = _ladder(compliance_matrix={"Art.13": "INSUFFICIENT_EVIDENCE"})

    assert _compute_final_verdict(state) == DISCLAIMER_OF_OPINION


def test_a_confirmed_non_conformity_outranks_the_floor():
    """A FAIL is a conclusion reached; too little delivered does not undo it."""
    state = _ladder(compliance_matrix={"Art.10": "FAIL"}, regulatory_coverage_pct=0.0,
                    completeness_score=0.0, intake_completeness_score=0.0)

    assert _compute_final_verdict(state) == FAIL
    assert state["opinion_disclaimer"] is False


@pytest.mark.parametrize("ics, cs, rc, expected", [
    (1.0, 1.0, 100.0, PASS),
    (0.85, 0.80, 80.0, PASS_WITH_OBSERVATIONS),
    (0.79, 1.0, 100.0, DISCLAIMER_OF_OPINION),
    (1.0, 0.74, 100.0, DISCLAIMER_OF_OPINION),
    (1.0, 1.0, 74.9, DISCLAIMER_OF_OPINION),
])
def test_the_clean_matrix_bands_are_unchanged(ics, cs, rc, expected):
    """Every all-PASS band behaves exactly as it did; only the order moved."""
    state = _ladder(intake_completeness_score=ics, completeness_score=cs,
                    regulatory_coverage_pct=rc)

    assert _compute_final_verdict(state) == expected
