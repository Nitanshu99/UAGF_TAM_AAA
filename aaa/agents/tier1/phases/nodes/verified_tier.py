"""Apply Phase 1's verified risk tier to the engagement, and re-solve the plan when it changed.

ScopeAgent returned ``verified_risk_tier`` and nothing read it: ``risk_tier`` kept
the declared value, and the plan solved before Phase 1 was never re-solved,
although ARCHITECTURE §6.2 runs the final plan against verified values
(T-20260913-081). A Phase 1 correction therefore changed no routing, scope or verdict.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def apply_verified_tier(state: dict) -> dict:
    """Adopt a verified tier that differs from ``risk_tier`` and re-plan against it.

    :param state: The AuditState dict after Phase 1's delta was applied.
    :returns: The state; ``risk_tier_correction`` records ``{declared, verified}``
        when the tier changed, and ``phase_plan`` is re-solved.
    """
    from aaa.agents.tier1.phases.nodes.plan import node_plan

    verified, current = state.get("verified_risk_tier"), state.get("risk_tier")
    if not verified or verified == current:
        return state
    state["risk_tier_correction"] = {"declared": current, "verified": verified}
    state["risk_tier"] = verified
    logger.warning("Engagement %s: Phase 1 verified risk tier %r (declared %r); "
                   "re-solving the phase plan.", state.get("engagement_id"), verified, current)
    return node_plan(state)
