"""Detail-section builders for the T14 governance-findings artefact."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest import IngestResult


def low_confidence_section(result: IngestResult) -> list[dict[str, Any]]:
    """Normalise the low-confidence controls flagged by ingest."""
    return [
        {
            "control_id": c.get("control_id", ""),
            "control_name": c.get("control_name", ""),
            "confidence": float(c.get("confidence", 0.0)),
            "flag_reason": c.get("flag_reason", ""),
        }
        for c in result.low_confidence_controls
    ]


def domains_section(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Summarise the CGSA domains for T14."""
    return [
        {
            "domain_id": d.get("domain_id", ""),
            "domain_name": d.get("domain_name", ""),
            "domain_score": float(d.get("domain_score", 0.0)),
            "domain_eu_ai_act_articles": list(d.get("domain_eu_ai_act_articles", []) or []),
            "controls_count": (
                len(d.get("controls", []) or []) if d.get("controls") is not None else None),
        }
        for d in (payload.get("domains", []) or [])
    ]


def hard_constraints_section(hard: dict[str, Any]) -> dict[str, Any]:
    """Normalise the hard-constraint solver results for T14."""
    return {
        "csp_satisfiable": bool(hard.get("csp_satisfiable", False)),
        "total_hard_constraints": hard.get("total_hard_constraints"),
        "violated_constraints": [
            {
                "control_id": v.get("control_id", ""),
                "control_name": v.get("control_name", ""),
                "required_score": int(v.get("required_score", 0)),
                "actual_score": int(v.get("actual_score", 0)),
                "score_delta": v.get("score_delta"),
                "eu_ai_act_article": v.get("eu_ai_act_article", ""),
                "violation_description": v.get("violation_description", ""),
            }
            for v in (hard.get("violated_constraints", []) or [])
        ],
    }
