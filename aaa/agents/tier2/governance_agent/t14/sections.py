"""Section builders for the T14 governance-findings artefact."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.t14.blocking import blocking_findings_section


def metadata_section(metadata: dict[str, Any]) -> dict[str, Any]:
    """Build ``cgsa_metadata`` from the payload metadata block."""
    return {
        "assessment_id": metadata.get("assessment_id", ""),
        "organisation_name": metadata.get("organisation_name", ""),
        "system_under_audit": metadata.get("system_under_audit", ""),
        "cgsa_version": metadata.get("cgsa_version", ""),
        "assessment_timestamp": metadata.get("assessment_timestamp", ""),
        "risk_tier": metadata.get("risk_tier", ""),
        "document_sources": list(metadata.get("document_sources", []) or []),
        "uagf_gmm_version": metadata.get("uagf_gmm_version"),
    }


def scores_section(scores: dict[str, Any]) -> dict[str, Any]:
    """Build ``overall_scores`` from the payload scores block."""
    return {
        "composite_maturity_score": scores.get("composite_maturity_score", 0.0),
        "composite_maturity_label": scores.get("composite_maturity_label", "absent"),
        "eu_ai_act_coverage_pct": scores.get("eu_ai_act_coverage_pct", 0.0),
        "csp_satisfiable": bool(scores.get("csp_satisfiable", False)),
        "governance_verdict": scores.get("governance_verdict", "non_compliant"),
        "controls_assessed": scores.get("controls_assessed"),
        "controls_meeting_threshold": scores.get("controls_meeting_threshold"),
        "controls_below_threshold": scores.get("controls_below_threshold"),
    }


def positive_findings_section(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise the CGSA positive findings for T14."""
    return [
        {
            "control_id": f.get("control_id", ""),
            "control_name": f.get("control_name", ""),
            "maturity_score": int(f.get("maturity_score", 0)),
            "finding": f.get("finding", ""),
        }
        for f in (handoff.get("positive_findings", []) or [])
    ]


__all__ = ["blocking_findings_section", "metadata_section", "positive_findings_section",
           "scores_section"]
