"""Part 6 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.aggregate_low_confidence import _aggregate_low_confidence  # noqa: F401
from aaa.tools.cgsa_ingest.logger import (  # noqa: F401
    _LOW_CONFIDENCE_THRESHOLD,
    _REQUIRED_TOP_LEVEL_KEYS,
    _VENDORED_SCHEMA,
    CGSAIngestError,
    IngestResult,
    logger,
)
from aaa.tools.cgsa_ingest.normalise_remediation import (  # noqa: F401
    _infer_harmonised_standards,
    _normalise_remediation,
)
from aaa.tools.cgsa_ingest.schema_validate import schema_validate  # noqa: F401
from aaa.tools.cgsa_ingest.shallow_required_check import _shallow_required_check  # noqa: F401


def _build_state_delta(payload: dict[str, Any], schema_version: str,
                       scores: dict[str, Any], handoff: dict[str, Any],
                       domains: list[dict[str, Any]], remediation: list[dict[str, Any]],
                       low_conf: list[dict[str, Any]],
                       risk_tier_match: bool | None) -> dict[str, Any]:
    """Assemble the §5.4 AuditState hydration map.

    A CSP failure overrides ``cgsa_phase5_verdict`` to FAIL, and the raw
    remediation roadmap is normalised into the typed AuditState shape.
    """
    state_delta: dict[str, Any] = {
        "cgsa_payload": payload,
        "cgsa_schema_version": schema_version,
        "cgsa_composite_maturity_score": scores.get("composite_maturity_score"),
        "cgsa_composite_maturity_label": scores.get("composite_maturity_label"),
        "cgsa_eu_ai_act_coverage_pct": scores.get("eu_ai_act_coverage_pct"),
        "cgsa_csp_satisfiable": scores.get("csp_satisfiable"),
        "cgsa_governance_verdict": scores.get("governance_verdict"),
        "cgsa_phase5_verdict": handoff.get("phase5_verdict"),
        "cgsa_phase5_narrative": handoff.get("phase5_narrative_summary"),
        "cgsa_blocking_findings": list(handoff.get("blocking_findings", []) or []),
        "cgsa_positive_findings": list(handoff.get("positive_findings", []) or []),
        "cgsa_low_confidence_controls": low_conf,
        "cgsa_recommended_follow_up": list(handoff.get("aaa_recommended_follow_up", []) or []),
        "cgsa_report_url": handoff.get("cgsa_report_url"),
        "cgsa_risk_tier_match": risk_tier_match,
        "harmonised_standards_applied": _infer_harmonised_standards(domains),
    }
    if scores.get("csp_satisfiable") is False:
        state_delta["cgsa_phase5_verdict"] = "FAIL"
    state_delta["remediation_roadmap"] = _normalise_remediation(remediation)
    return state_delta
