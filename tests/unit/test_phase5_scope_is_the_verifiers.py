"""T-20260914-055: Phase 5 judges scope against the binding articles the Verifier is given.

Case 06's wizard run (evaluated CGSA export) wrote in T14 that the self-assessment maps
controls to Art.50 among others, "which do not bind it", while the Verifier's
``binding_articles`` listed Art.50 (Stage A gate ``triggers_art50_transparency``). T14 was
refused as a material contradiction; Phase 5 had judged scope from the tier alone.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.scope_context import with_engagement_scope
from aaa.agents.tier2.governance_agent.scope_note import cgsa_scope_note
from aaa.agents.tier2.governance_agent.t15.applicability import unbound_blocks
from aaa.tools.regulatory_coverage.binding import binding_articles, binds, scope_known

_STATE = {"risk_tier": "high", "is_llm_or_agentic": True,
          "scope_gate": {"triggers_art50_transparency": True},
          "client_submission": {"stage_a": {"gpai_general_purpose": False}}}
_PAYLOAD = {"eu_ai_act_compliance_matrix": {
    "article_9": {}, "article_50": {}, "article_16": {}, "article_73": {}}}


def test_the_dispatched_list_is_the_verifiers() -> None:
    """One computation feeds both the Phase 5 dispatch and the Verifier's review input."""
    listed = binding_articles(_STATE)
    assert listed is not None and "Art.50" in listed and "Art.16" not in listed
    assert with_engagement_scope({}, _STATE, "P5")["engagement_scope"]["binding_articles"] == listed


def test_a_gate_scoped_article_is_not_called_unbound() -> None:
    """Art.50 binds through the gate; Art.16 and Art.73 are outside the binding set."""
    scope = {"risk_tier": "high", "binding_articles": binding_articles(_STATE)}
    note = cgsa_scope_note(_PAYLOAD, scope)
    assert "maps controls to Art.16, Art.73; none of these is among this engagement's " \
           "binding_articles" in note and "do not bind" not in note
    assert "Art.50" not in note and "Art.9" not in note


def test_sub_articles_and_aliases_bind_through_their_article() -> None:
    """``Art.10§5`` binds when ``Art.10`` does; ``Art.51`` is ``GPAI_51``."""
    scope = {"binding_articles": ["Art.10", "GPAI_51"]}
    assert binds(scope, "Art.10§5") and binds(scope, "Art.51") and not binds(scope, "Art.12")


def test_without_a_list_the_tier_still_decides() -> None:
    """Callers that pass a state-like tier keep the engagement-scope reading."""
    assert scope_known({"risk_tier": "limited"}) and not scope_known({})
    assert binds({"risk_tier": "limited"}, "Art.13") and not binds({"risk_tier": "limited"}, "Art.9")
    assert binding_articles({}) is None


def test_t15_follows_the_dispatched_list() -> None:
    """An empty binding list (minimal tier, no gate) marks every T15 block not applicable."""
    assert unbound_blocks({"binding_articles": []}) == {
        "art12_record_keeping", "art17_qms", "art72_post_market_plan"}
    assert unbound_blocks({"binding_articles": binding_articles(_STATE)}) == set()
