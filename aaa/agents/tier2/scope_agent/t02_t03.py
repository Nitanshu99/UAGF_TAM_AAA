"""T02 system-card and T03 Annex III mapping artefact builders."""
from __future__ import annotations

from aaa.agents.tier2.scope_agent.t02_summary import phase1_summary
from aaa.agents.tier2.scope_agent.uncorroborated import uncorroborated, uncorroborated_note
from aaa.platform.state import AnnexIIIEntry


def build_t02(engagement_id: str, t01a: dict, verified_modality: str, is_llm: bool,
              verification_map: dict, gpai_result: str | None, art5: bool,
              now: str) -> dict:
    """Build the T02 system-card payload."""
    return {
        "engagement_id": engagement_id,
        "provider_name": t01a.get("provider_name", ""),
        "deployer_name": t01a.get("deployer_name"),
        "system_name": t01a.get("system_name", ""),
        "version": t01a.get("version", ""),
        "intended_purpose": t01a.get("intended_purpose", ""),
        "declared_modality": t01a.get("declared_modality", ""),
        "verified_modality": verified_modality,
        "deployment_context": t01a.get("deployment_context", ""),
        "is_llm_or_agentic": is_llm,
        "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
        "gdpr_overlap": t01a.get("gdpr_overlap", False),
        "special_category_data": t01a.get("special_category_data", False),
        "declaration_verification": verification_map,
        "phase1_summary": phase1_summary(t01a, verified_modality, verification_map,
                                         gpai_result, art5),
        "art5_prohibited": art5,
        "gpai_screening_result": gpai_result,
        "generated_at": now,
    }


def build_t03(engagement_id: str, entries: list[AnnexIIIEntry],
              verified_risk_tier: str, art5: bool, now: str, transparency: str = "") -> dict:
    """Build the T03 Annex III mapping payload.

    :param transparency: The Art. 50 finding the tier rests on (``t04.transparency_basis``),
        stated here so the narrative says whether a trigger is declared rather than naming
        Art. 50 as a basis — read as a contradiction beside a minimal tier (T-20260913-090).
    """
    return {
        "engagement_id": engagement_id,
        "entries": [dict(e) for e in entries],
        "verified_risk_tier": verified_risk_tier,
        "art5_prohibited": art5,
        # Cites the classification rule and names where the tier's basis is recorded (T-086).
        "classification_narrative": (
            f"{len(entries)} Annex III section(s) identified under Art. 6(2) and Annex III"
            f"{'' if entries else ' — none applies'}. "
            f"{'Risk tier' if uncorroborated(entries) else 'Verified risk tier'}: "
            f"{verified_risk_tier}{transparency}.{uncorroborated_note(entries, verified_risk_tier)}"
            " The decision is recorded in T04_risk_tier_decision."
        ),
        "generated_at": now,
    }
