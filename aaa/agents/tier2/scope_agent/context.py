"""Processing-context assembly for the Phase 1 workflow."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.scope_agent.checks import gpai_screen


def build_context(engagement_id: str, t01a: dict, message: dict, system_desc: str,
                  annex_entries: list, verification_map: dict, verified_modality: str,
                  verified_risk_tier: str, verified_sections: list,
                  is_llm_or_agentic: bool, art5_prohibited: bool, art43: dict,
                  preview_procedure: Any, art43_delta: bool,
                  pseudo_state: dict) -> dict[str, Any]:
    """Bundle every Phase 1 intermediate into one context mapping."""
    return {
        "engagement_id": engagement_id, "t01a": t01a,
        "annex_entries": annex_entries, "verification_map": verification_map,
        "verified_modality": verified_modality, "verified_risk_tier": verified_risk_tier,
        "verified_sections": verified_sections, "is_llm_or_agentic": is_llm_or_agentic,
        "gpai_result": gpai_screen(t01a, system_desc),
        "art5_prohibited": art5_prohibited,
        "art43": art43, "preview_procedure": preview_procedure,
        "art43_delta": art43_delta, "pseudo_state": pseudo_state,
        "evidence_uris": message.get("evidence_uris", []),
    }


def computed_evidence(ctx: dict[str, Any], system_desc: str) -> dict[str, Any]:
    """Shape the deterministic evidence handed to the Phase 1 prompt."""
    return {
        "system_description": system_desc,
        "annex_iii_mapping": [dict(e) for e in ctx["annex_entries"]],
        "verification_map": ctx["verification_map"],
        "verified_modality": ctx["verified_modality"],
        "verified_risk_tier": ctx["verified_risk_tier"],
        "art43_decision": ctx["art43"],
        "gpai_result": ctx["gpai_result"],
    }
