"""Option A for T-20260913-075, and the verified tier finally applied (T-20260913-081).

Case 02 declared ``limited`` with Art. 50 triggers ``['none']``: the tier verifies
as ``minimal``, the engagement adopts it and re-plans, the supplied model is still
examined (Art. 95), and findings against articles that do not bind are observations.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.compliance_matrix.out_of_scope_findings import (
    restate_out_of_scope_findings,
)
from aaa.agents.tier1.phases.nodes.verified_tier import apply_verified_tier
from aaa.agents.tier2.scope_agent.checks import determine_risk_tier
from aaa.agents.tier2.scope_agent.t04 import build_t04
from aaa.tools.findings import make_finding


def test_limited_and_minimal_follow_the_declared_art50_triggers() -> None:
    assert determine_risk_tier("limited", [], False, art50_triggered=False) == "minimal"
    assert determine_risk_tier("minimal", [], False, art50_triggered=True) == "limited"
    assert determine_risk_tier("limited", ["4"], False, art50_triggered=False) == "high"
    assert determine_risk_tier("limited", [], False) == "limited", "no triggers carried: declared stands"


def test_t04_states_the_transparency_basis() -> None:
    rationale = build_t04("e", "limited", "minimal", False, [], "now",
                          {"art50_transparency_triggers": ["none"]})["risk_tier_rationale"]
    assert "transparency obligations do not apply" in rationale


def _state(**over: Any) -> dict[str, Any]:
    base = {"engagement_id": "eng-02", "risk_tier": "limited", "verified_risk_tier": "minimal",
            "modality": "time_series", "is_llm_or_agentic": False, "annex_iii_mapping": [],
            "phase_artefacts": {},
            "client_submission": {"stage_b": {"model_artifact_uri": "minio://m.joblib",
                                              "evaluation_dataset_uri": "minio://e.csv"}}}
    return {**base, **over}


def test_the_verified_tier_replaces_the_declared_one_and_the_plan_follows() -> None:
    state = apply_verified_tier(_state())
    assert state["risk_tier"] == "minimal"
    assert state["risk_tier_correction"] == {"declared": "limited", "verified": "minimal"}
    assert state["phase_plan"]["P3"] == "M" and "Art. 95" in state["phase_plan_rationale"]["P3"]


def test_an_unchanged_tier_leaves_the_plan_alone() -> None:
    state = apply_verified_tier(_state(verified_risk_tier="limited"))
    assert "phase_plan" not in state and "risk_tier_correction" not in state


def test_a_finding_on_articles_that_do_not_bind_is_an_observation() -> None:
    state = {"risk_tier": "minimal", "blocking_findings": [make_finding(
        finding_id="P3-TARGET-FNR", materiality="material", articles=["Art.15"], source_phase="P3",
        description="Measured false-negative rate 0.269 exceeds the declared target.",
        recommendation="r")]}
    restate_out_of_scope_findings(state)
    finding = state["blocking_findings"][0]
    assert finding["materiality"] == "observation"
    assert "Art.15 does not bind this 'minimal' engagement" in finding["description"]

    high = {"risk_tier": "high", "blocking_findings": [make_finding(
        finding_id="x", materiality="material", articles=["Art.15"], source_phase="P3",
        description="d", recommendation="r")]}
    restate_out_of_scope_findings(high)
    assert high["blocking_findings"][0]["materiality"] == "material"


def test_a_tier_correction_is_cited_and_explained_in_t04_and_t05() -> None:
    """Case 02 p1a1: the Verifier escalated T04/T05 for an unsourced, uncited correction."""
    from aaa.agents.tier2.scope_agent.t04_t05 import build_t05

    t04 = build_t04("e", "limited", "minimal", False, [], "now", {"art50_transparency_triggers": ["none"]})
    assert "EU AI Act Art. 50" in t04["regulatory_rag_citations"]
    assert "declared in Stage A (T01a" in t04["risk_tier_rationale"]
    t05 = build_t05("e", {"procedure": "not_applicable", "rationale": "No Art. 43 route."}, None,
                    False, {"risk_tier": "minimal"}, "now", "limited")
    assert "follows the Phase 1 verified risk tier 'minimal'" in t05["rationale"]
    same = build_t05("e", {"procedure": "not_applicable", "rationale": "r"}, None, False,
                     {"risk_tier": "high"}, "now", "high")
    assert same["rationale"] == "r"


def test_the_verifier_is_told_the_verified_scope_and_the_phase_basis() -> None:
    """Case 02: T09–T13 were judged against high-risk duties the review input implied."""
    from aaa.agents.tier1.phases.verification.scope_context import with_engagement_scope

    state = {"risk_tier": "minimal", "risk_tier_correction": {"declared": "limited", "verified": "minimal"},
             "phase_plan_rationale": {"P3": "examined voluntarily (Art. 95)"}}
    summary = with_engagement_scope({"declared_risk_tier": "limited"}, state, "P3")
    scope = summary["engagement_scope"]
    assert scope["risk_tier"] == "minimal" and scope["binding_articles"] == []
    assert scope["phase_basis"] == "examined voluntarily (Art. 95)"
    assert with_engagement_scope({"a": 1}, {}, "P3") == {"a": 1}


def test_t11_and_t03_say_what_actually_ran_and_why() -> None:
    from aaa.agents.tier2.model_validator.t11 import build_t11
    from aaa.agents.tier2.scope_agent.t02_t03 import build_t03

    t11 = build_t11("e", "time_series", {"overall_robustness_verdict": "NOT_TESTED",
                                          "skipped_reason": "the target is continuous"}, "now")
    assert t11["art15_compliance_notes"].startswith("Robustness probes were not executed")
    assert "Art. 6(2)" in build_t03("e", [], "minimal", False, "now")["classification_narrative"]


def test_phase_1_reviews_see_the_verified_tier_and_t03_states_the_art50_finding() -> None:
    """Case 02 p1a3: Phase 1 critiques saw the declared scope; T03 read as contradicting itself."""
    from aaa.agents.tier1.phases.verification.scope_context import with_engagement_scope
    from aaa.agents.tier2.scope_agent.t02_t03 import build_t03
    from aaa.agents.tier2.scope_agent.t04 import transparency_basis

    scope = with_engagement_scope({}, {"risk_tier": "limited", "verified_risk_tier": "minimal"},
                                  "P1")["engagement_scope"]
    assert scope["risk_tier"] == "minimal" and scope["binding_articles"] == []
    assert scope["risk_tier_correction"] == {"declared": "limited", "verified": "minimal"}
    basis = transparency_basis({"art50_transparency_triggers": ["none"]}, "minimal")
    narrative = build_t03("e", [], "minimal", False, "now", basis)["classification_narrative"]
    assert "transparency obligations do not apply" in narrative


def test_a_compliance_note_says_when_its_article_does_not_bind() -> None:
    """Case 02: T06 cited Art. 10 as its basis for a minimal-risk engagement; the Verifier ordered a rerun."""
    from aaa.tools.regulatory_coverage.binding_notes import annotate_non_binding

    artefact = {"art10_compliance_notes": "Data examined per Art. 10 §2–3.",
                "art10_2f_compliance_notes": "Bias examination.", "other_notes": "untouched"}
    annotate_non_binding(artefact, "minimal")
    assert "Art. 10 does not bind this 'minimal' engagement" in artefact["art10_compliance_notes"]
    assert "voluntary examination (Art. 95)" in artefact["art10_2f_compliance_notes"]
    assert artefact["other_notes"] == "untouched"
    high = {"art10_compliance_notes": "Data examined per Art. 10 §2–3."}
    annotate_non_binding(high, "high")
    assert high["art10_compliance_notes"] == "Data examined per Art. 10 §2–3."
    unknown = {"art13_compliance_notes": "x"}
    annotate_non_binding(unknown, None)
    assert unknown["art13_compliance_notes"] == "x"
