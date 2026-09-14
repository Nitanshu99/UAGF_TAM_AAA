"""What the Verifier must know about the engagement's scope to judge an artefact against it.

Case 02 (clean loop, 2026-09-13) verified as minimal-risk and examined its model
voluntarily (Art. 95), but the review input carried only the *declared* 'limited'
tier. The Verifier then escalated T07 and T09–T13 against high-risk obligations
that bind nothing here (T-20260913-086).
"""
from __future__ import annotations

from typing import Any

from aaa.tools.regulatory_coverage.binding import binding_articles


def with_engagement_scope(summary: dict[str, Any], state: dict[str, Any],
                          phase_id: str) -> dict[str, Any]:
    """*summary* plus ``engagement_scope``: verified tier, correction, binding articles, phase basis.

    :param summary: The dispatch's declaration summary.
    :param state: The AuditState.
    :param phase_id: The phase whose artefact is under review (``P3`` …).
    """
    # Phase 1's artefacts are reviewed before the verified tier is applied (T-090):
    # judge against the verified tier as soon as Phase 1 has produced one.
    verified, declared = state.get("verified_risk_tier"), state.get("risk_tier")
    binding = binding_articles(state)
    if binding is None:
        return summary
    correction = state.get("risk_tier_correction") or (
        {"declared": declared, "verified": verified} if verified and verified != declared else None)
    basis = (state.get("phase_plan_rationale") or {}).get(phase_id)
    return {**summary, "engagement_scope": {
        "risk_tier": verified or declared,
        "risk_tier_correction": correction,
        "binding_articles": binding,
        "phase_basis": basis,
        "note": ("Judge the artefact against the obligations that bind this engagement; an "
                 "article outside binding_articles does not apply to it."),
    }}
