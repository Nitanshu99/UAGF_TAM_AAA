"""T-20260914-018: T14 says the CGSA's own risk tier is the partner's, beside the engagement's."""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.scope_note import cgsa_scope_note

_PAYLOAD = {"metadata": {"risk_tier": "limited"},
            "eu_ai_act_compliance_matrix": {"article_9": {}, "article_50": {}}}


def test_a_different_partner_tier_is_named_as_the_assessments_own() -> None:
    """Case 02: assessed as limited, verified minimal."""
    note = cgsa_scope_note(_PAYLOAD, {"risk_tier": "minimal"})
    assert "made against a 'limited' risk tier" in note and "verified tier is 'minimal'" in note


def test_the_same_tier_or_unknown_scope_adds_no_tier_sentence() -> None:
    """Nothing to reconcile, nothing said."""
    assert "made against" not in cgsa_scope_note(_PAYLOAD, {"risk_tier": "limited"})
    assert cgsa_scope_note(_PAYLOAD, {}) == ""
