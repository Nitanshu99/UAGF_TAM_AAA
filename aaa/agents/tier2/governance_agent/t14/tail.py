"""Tail sections (follow-up, risk-tier match, spawns) for T14."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest import IngestResult


def tail_sections(
    result: IngestResult,
    decl: dict[str, Any],
    spawn: dict[str, Any],
    risk_tier_mismatch: bool,
    metadata: dict[str, Any],
    handoff: dict[str, Any],
) -> dict[str, Any]:
    """Build the follow-up / risk-tier / spawn sections of T14."""
    return {
        "aaa_recommended_follow_up": [
            {
                "recommendation": f.get("recommendation", ""),
                "rationale": f.get("rationale", ""),
                "urgency": f.get("urgency"),
            }
            for f in (handoff.get("aaa_recommended_follow_up", []) or [])
        ],
        "risk_tier_match": {
            "match": not risk_tier_mismatch
                and result.state_delta.get("cgsa_risk_tier_match") is not False,
            "phase1_risk_tier": decl.get("risk_tier", ""),
            "cgsa_risk_tier": metadata.get("risk_tier", ""),
            "hitl_triggered": risk_tier_mismatch,
        },
        "tier3_spawn_recommendations": {
            "cyber_spawn": spawn["cyber_spawn"],
            "cyber_rationale": spawn["cyber_rationale"],
            "privacy_spawn": spawn["privacy_spawn"],
            "privacy_rationale": spawn["privacy_rationale"],
        },
        "cgsa_report_url": handoff.get("cgsa_report_url"),
        "hitl_required": False,
        "hitl_reason": None,
    }
