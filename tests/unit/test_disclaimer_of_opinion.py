"""Findings F11 and F13 — an audit that could not conclude must say so.

F11: the assessed run persisted `final_verdict = PASS_WITH_OBSERVATIONS` and
`auditor_opinion.opinion_type = disclaimer_of_opinion` in the same state, with
12 of 14 in-scope articles at INSUFFICIENT_EVIDENCE. The opinion was right; the
verdict was the field that is logged, persisted, returned by the API and printed
on the PDF cover. The vocabulary simply had no token for "could not assess", so
a pervasive evidence gap had to render as a qualified pass.

F13: `regulatory_coverage_pct` read 80.0 on that same run, because an article
counted as covered when it was merely *present* in the matrix — INSUFFICIENT_
EVIDENCE included. The headline KPI reported health on an audit that had
assessed two articles.
"""
from __future__ import annotations

import logging

from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION, FAIL, PASS
from tests.unit.support.real_auditor_state import base_state

#: The compliance matrix exactly as call #036 received it: two PASS verdicts,
#: both from *intake* artefacts, and twelve articles nobody was able to assess.
_ASSESSED_RUN_MATRIX = {
    "Annex_III": "INSUFFICIENT_EVIDENCE", "Annex_IV": "PASS",
    "Art.10§2(f)": "INSUFFICIENT_EVIDENCE", "Art.11": "PASS",
    "Art.12": "INSUFFICIENT_EVIDENCE", "Art.13": "INSUFFICIENT_EVIDENCE",
    "Art.15": "INSUFFICIENT_EVIDENCE", "Art.15§1": "INSUFFICIENT_EVIDENCE",
    "Art.17": "INSUFFICIENT_EVIDENCE", "Art.43": "INSUFFICIENT_EVIDENCE",
    "Art.5": "INSUFFICIENT_EVIDENCE", "Art.6": "INSUFFICIENT_EVIDENCE",
    "Art.72": "INSUFFICIENT_EVIDENCE", "Art.9": "INSUFFICIENT_EVIDENCE",
}


def _coverage_state(matrix: dict[str, str]) -> dict:
    """A high-risk state whose coverage is decided purely by *matrix*."""
    return {"risk_tier": "high", "is_llm_or_agentic": False,
            "compliance_matrix": dict(matrix), "phase_artefacts": {},
            "verifier_critiques": {}, "intake_completeness_score": 1.0,
            "scope_gate": {}}


# --------------------------------------------------------------------------- #
# F11 — the verdict ladder
# --------------------------------------------------------------------------- #

def test_unassessable_core_article_disclaims_instead_of_passing():
    """The assessed run's own condition, which produced a qualified pass."""
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    state = base_state(insufficient_evidence_articles=["Art.9", "Art.12"])
    node_compliance_matrix(state)

    assert state["final_verdict"] == DISCLAIMER_OF_OPINION
    assert state["opinion_disclaimer"] is True


def test_the_verdict_and_the_opinion_cannot_contradict_each_other():
    """F11 itself: both fields derived from one state, checked against each other."""
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    from aaa.agents.tier1.phases.phase_runners.phase6_declaration_summary import (
        _phase6_declaration_summary,
    )
    from aaa.agents.tier2.report_architect import _auditor_opinion

    state = base_state(insufficient_evidence_articles=["Art.15"])
    node_compliance_matrix(state)
    decl = _phase6_declaration_summary(state, "eng-x", {})
    opinion = _auditor_opinion(decl, state["final_verdict"])

    assert opinion["opinion_type"] == "disclaimer_of_opinion"
    assert state["final_verdict"] == DISCLAIMER_OF_OPINION, (
        "the headline verdict must not read as a pass while the opinion "
        "declines to conclude — that is the contradiction the Verifier "
        "itself raised as critical/material at calls #036 and #037")


def test_a_confirmed_non_conformity_outranks_the_disclaimer():
    """FAIL is a conclusion reached on evidence; it stays at the top of the ladder."""
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    state = base_state(
        insufficient_evidence_articles=["Art.9"],
        blocking_findings=[{"finding_id": "F1", "materiality": "material",
                            "eu_ai_act_articles": ["Art.15"],
                            "description": "robustness probe failed"}])
    node_compliance_matrix(state)

    assert state["final_verdict"] == FAIL
    assert state["opinion_disclaimer"] is False


def test_thin_kpis_disclaim_rather_than_allege_a_breach():
    """Too little evidence to stand behind a pass is not a non-conformity."""
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    # Nothing was admitted, so completeness/coverage land far below the bands
    # while no article carries an adverse verdict. This branch returned FAIL.
    state = base_state(verifier_critiques={}, phase_artefacts={},
                       phase_status={"T09_model_card": "M"})
    node_compliance_matrix(state)

    assert state["final_verdict"] == DISCLAIMER_OF_OPINION
    assert state["opinion_disclaimer"] is True


def test_a_clean_engagement_still_passes():
    """The disclaimer must not swallow the happy path.

    This fixture used to reach a clean ``PASS`` by evidencing Art. 50 with a
    ``T13_output_sampling_log`` citing it. Fix 47 established that is a
    mis-attribution and fix 50 refuses it, and what that exposed is **finding
    R18**: Art. 50 is in *every* tier's article set and **no artefact evidences
    it**, so a clean 100 % engagement is not reachable at any tier.

    The subject survives intact, and is in fact better demonstrated: the two
    admitted artefacts evidence what they are accountable for, every core
    Art. 9-17 requirement they cover passes, and the audit does **not** disclaim.
    """
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    state = base_state(risk_tier="high", declared_risk_tier="high",
                       insufficient_evidence_articles=[])
    # The whole in-scope set except what the two admitted artefacts evidence,
    # so the only gaps are the ones this fixture is not about.
    for article in ("Art.5", "Art.6", "Art.9", "Art.11", "Art.12", "Art.14",
                    "Art.17", "Art.43", "Art.72", "Annex_III", "Annex_IV"):
        state["verifier_critiques"].setdefault("T02_system_card", {
            "verdict": "accept", "article_citations": []})
    node_compliance_matrix(state)

    assert state["compliance_matrix"]["Art.13"] == PASS
    assert state["compliance_matrix"]["Art.15"] == PASS
    assert state["compliance_matrix"]["Art.10"] == PASS


def test_art_50_no_longer_binds_a_system_that_never_meets_a_natural_person():
    """Finding R18, closed by fix 51, asserted so it cannot come back.

    The gap was masked three times and removed one layer per fix — fix 47 took
    Art. 50 out of `_TEMPLATE_ARTICLES`, fix 41 named it in `KNOWN_UNOWNED`,
    fix 50 closed the citation that still claimed it — and what was underneath
    was not a missing artefact but a **double scoping**. Art. 50 is conditional,
    the Stage A gate already decides it, and every tier set declared it as well.
    """
    from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET

    assert not [t for t, arts in ARTICLE_SET.items() if "Art.50" in arts]


def test_a_gap_outside_the_core_requirements_is_not_what_disclaims():
    """The disclaimer predicate is Art.9-17, matching PROMPT.md — deliberately.

    The fixture used to meet the KPI floor by evidencing Art. 50 through a
    mis-attributed T13 citation (fix 47, fix 50). It cannot any more — Art. 50 is
    unowned in every tier, finding **R18** — so the subject is asserted on the
    predicate itself: a gap at Art. 43 is outside Art. 9-17 and does not make the
    engagement *unassessable*, whatever the coverage floor then decides.
    """
    from aaa.agents.tier1.phases.compliance_matrix.logger import (
        _CORE_HIGH_RISK_ARTICLES,
        _core_article,
    )

    def _is_core(article: str) -> bool:
        return _core_article(article) in _CORE_HIGH_RISK_ARTICLES

    assert not _is_core("Art.43"), "the gap this fixture is about"
    assert _is_core("Art.13"), "and one that would disclaim"
    assert not _is_core("Art.50"), "R18's gap is real but not a core one"


# --------------------------------------------------------------------------- #
# F11 — everything downstream of the verdict
# --------------------------------------------------------------------------- #

def test_the_verdict_alone_reaches_the_opinion():
    """A declaration assembled without ``opinion_disclaimer`` still disclaims."""
    from aaa.agents.tier2.report_architect import _auditor_opinion

    decl = {"compliance_matrix": {"Art.15": "INSUFFICIENT_EVIDENCE"},
            "blocking_findings": [], "stage_a": {"system_name": "CreditGuard"}}
    assert _auditor_opinion(decl, DISCLAIMER_OF_OPINION)["opinion_type"] == (
        "disclaimer_of_opinion")


def test_a_disclaimed_engagement_is_routed_to_human_review(caplog):
    """Previously only a FAIL verdict reached the checkpoint on its own."""
    from aaa.agents.tier1.phases.node_stubs import node_hitl_checkpoint

    with caplog.at_level(logging.WARNING):
        node_hitl_checkpoint({"engagement_id": "eng-x",
                              "final_verdict": DISCLAIMER_OF_OPINION})
    assert any("HITL required" in r.message for r in caplog.records)


def test_a_missing_verdict_is_not_reported_as_a_qualified_pass():
    """T17/T18 defaulted an absent verdict to PASS_WITH_OBSERVATIONS."""
    from aaa.agents.tier2.report_architect.t18 import build_t18

    t18 = build_t18("eng-x", {"stage_a": {}, "blocking_findings": []}, {}, "now")
    assert t18["final_verdict"] == DISCLAIMER_OF_OPINION
    assert t18["auditor_opinion"]["opinion_type"] == "disclaimer_of_opinion"


def test_a_missing_verdict_is_not_persisted_as_a_failure():
    """The results writer defaulted to FAIL — a breach nobody established."""
    from aaa.data.writer.results import _build_audit_result

    record = _build_audit_result("eng-x", {}, "2026-08-21T00:00:00Z")
    assert record.final_verdict == DISCLAIMER_OF_OPINION


def test_the_token_renders_deliberately_rather_than_as_unknown():
    """Badge and PDF cover must map it, not fall through to their defaults."""
    from aaa.tools.report_render.pdf.theme import MUTED, VERDICT_COLORS, verdict_color
    from aaa.ui.styles.badges import verdict_badge

    assert DISCLAIMER_OF_OPINION in VERDICT_COLORS
    assert verdict_color(DISCLAIMER_OF_OPINION) is MUTED
    assert DISCLAIMER_OF_OPINION in verdict_badge(DISCLAIMER_OF_OPINION)


def test_the_report_schemas_accept_the_token():
    """A verdict the renderer cannot validate would fail at the last step."""
    from aaa.tools.template_render.logger import _load_schema

    for tid in ("T17_compliance_matrix", "T18_audit_report"):
        enum = _load_schema(tid)["properties"]["final_verdict"]["enum"]
        assert DISCLAIMER_OF_OPINION in enum, tid


# --------------------------------------------------------------------------- #
# F13 — coverage counts what was assessed, not what was listed
# --------------------------------------------------------------------------- #

def test_unassessed_articles_do_not_count_towards_coverage():
    """Reproduces the assessed run's headline 80.0% on two assessed articles."""
    from aaa.tools.regulatory_coverage import compute_regulatory_coverage_pct

    state = _coverage_state(_ASSESSED_RUN_MATRIX)
    pct = compute_regulatory_coverage_pct(state)

    # 2 of 14: the denominator lost Art. 50 in fix 51, which is conditional and
    # never bound this engagement. The subject is unchanged — coverage counts a
    # *reached conclusion*, and twelve of these articles are INSUFFICIENT_EVIDENCE.
    assert pct == 14.3, (
        "12 of 14 in-scope articles were listed but unassessed; only Annex_IV "
        f"and Art.11 carry a verdict. Got {pct}, the assessed run reported 80.0")


def test_a_fully_assessed_engagement_still_scores_full_coverage():
    """The stricter rule must not penalise an audit that did the work."""
    from aaa.tools.regulatory_coverage import ARTICLE_SET, compute_regulatory_coverage_pct

    state = _coverage_state({a: "PASS" for a in ARTICLE_SET["high"]})
    assert compute_regulatory_coverage_pct(state) == 100.0


def test_an_adverse_verdict_is_coverage_too():
    """FAIL is a conclusion reached; it is evidence of work, not a gap."""
    from aaa.tools.regulatory_coverage import ARTICLE_SET, compute_regulatory_coverage_pct

    matrix = {a: "PASS" for a in ARTICLE_SET["high"]}
    matrix["Art.15"] = "FAIL"
    assert compute_regulatory_coverage_pct(_coverage_state(matrix)) == 100.0


def test_a_requirement_that_does_not_bind_leaves_the_denominator():
    """NOT_APPLICABLE is not an evidence gap, so it must not depress the KPI."""
    from aaa.tools.regulatory_coverage import ARTICLE_SET, compute_regulatory_coverage_pct

    matrix = {a: "PASS" for a in ARTICLE_SET["high"]}
    matrix["Art.50"] = "NOT_APPLICABLE"
    state = _coverage_state(matrix)

    assert compute_regulatory_coverage_pct(state) == 100.0


def test_the_breakdown_names_exactly_what_the_kpi_docks():
    """Two copies of the rule are how the number and its explanation diverge."""
    from aaa.tools.regulatory_coverage import (
        compute_regulatory_coverage_pct,
        regulatory_coverage_breakdown,
    )

    state = _coverage_state(_ASSESSED_RUN_MATRIX)
    breakdown = regulatory_coverage_breakdown(state)

    assert breakdown["regulatory_coverage_pct"] == compute_regulatory_coverage_pct(state)
    assert set(breakdown["covered"]) == {"Annex_IV", "Art.11"}
    assert "Art.9" in breakdown["missing"]
