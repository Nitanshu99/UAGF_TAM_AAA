"""T04 — the Annex III mapping the scope gate produced."""
from __future__ import annotations


def build_t04(engagement_id: str, declared_tier: str, verified_tier: str,
              art5: bool, verified_sections: list[str], now: str,
              t01a: dict | None = None) -> dict:
    """Build the T04 risk-tier decision payload.

    The Art. 6(3) derogation is recorded as the provider declared it. It was
    hardcoded ``false``, so a provider claiming the derogation was recorded as
    not claiming it (T-20260913-037). Whether it is accepted is a judgement this
    builder does not make: ``art6_derogation_accepted`` stays ``None``.
    """
    stage_a = t01a or {}
    return {
        "engagement_id": engagement_id,
        "declared_risk_tier": declared_tier,
        "verified_risk_tier": verified_tier,
        "risk_tier_rationale": (
            f"Declared tier: {declared_tier}. "
            f"Verified tier: {verified_tier} based on confirmed Annex III sections: "
            f"{verified_sections or 'none'}" + transparency_basis(stage_a, verified_tier) + "."
        ),
        "art5_prohibited": art5,
        "art5_prohibition_basis": None,
        "art6_derogation_claimed": bool(stage_a.get("art6_derogation_claimed")),
        "art6_derogation_rationale": stage_a.get("art6_derogation_rationale") or None,
        "art6_derogation_accepted": None,
        "annex_iii_sections_verified": verified_sections,
        # Art. 50 is cited when the tier rests on the transparency triggers (T-20260913-084).
        "regulatory_rag_citations": ["EU AI Act Art. 6", "EU AI Act Annex III"]
        + (["EU AI Act Art. 50"] if transparency_basis(stage_a, verified_tier) else []),
        "generated_at": now,
    }


def transparency_basis(stage_a: dict, verified_tier: str) -> str:
    """Name the Art. 50 triggers a ``limited`` / ``minimal`` verdict rests on (T-20260913-075)."""
    if verified_tier not in {"limited", "minimal"} or "art50_transparency_triggers" not in stage_a:
        return ""
    triggers = [t for t in stage_a.get("art50_transparency_triggers") or [] if t != "none"]
    return (f"; Art. 50 transparency triggers declared in Stage A (T01a "
            f"art50_transparency_triggers): {', '.join(triggers) or 'none'}, so transparency "
            f"obligations {'apply' if triggers else 'do not apply'}")


__all__ = ["build_t04", "transparency_basis"]
