"""
cgsa_ingest — validate the pulled CGSA payload and map every §5.4 field
into the AAA ``AuditState`` (§4.5).

Workflow:

  1. ``schema_validate(payload, "1.0.0")`` against the vendored
     ``data/files/uagf_cgsa_aaa_schema.json``.  Failure ⇒ raises
     ``CGSAIngestError`` so the GovernanceAgent can ``escalate_hitl``.
  2. Map the payload into the typed ``CGSAPayload`` shape (§5.4
     consumption map — every required field is consumed, nothing dropped).
  3. Surface low-confidence controls (``confidence < 0.6``) and CSP
     failures (``csp_satisfiable = false``) for downstream HITL flagging.

The function returns an ``IngestResult`` dataclass containing both the
validated payload and a ``state_delta`` dict ready to be merged into
``AuditState``.
"""
from __future__ import annotations

import json
import logging
import pathlib
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Vendored schema path — module-relative so the tool is portable.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_VENDORED_SCHEMA = _REPO_ROOT / "data" / "files" / "uagf_cgsa_aaa_schema.json"

_LOW_CONFIDENCE_THRESHOLD = 0.6
_REQUIRED_TOP_LEVEL_KEYS = (
    "metadata",
    "overall_scores",
    "domains",
    "eu_ai_act_compliance_matrix",
    "hard_constraint_results",
    "remediation_roadmap",
    "aaa_phase5_handoff",
)


class CGSAIngestError(Exception):
    """Raised when the CGSA payload fails validation or mapping."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[cgsa_ingest] {reason}")


@dataclass
class IngestResult:
    """Output of ``cgsa_ingest`` — validated payload + state delta."""

    payload: dict[str, Any]
    state_delta: dict[str, Any]
    low_confidence_controls: list[dict[str, Any]] = field(default_factory=list)
    schema_errors: list[str] = field(default_factory=list)
    schema_version: str = "1.0.0"


def schema_validate(
    payload: dict[str, Any],
    schema_version: str = "1.0.0",
    schema_path: pathlib.Path | None = None,
) -> list[str]:
    """
    Validate ``payload`` against the vendored CGSA schema.

    Returns a list of error messages (empty ⇒ valid).
    Uses ``jsonschema`` when available; otherwise applies a minimal
    required-keys check so offline runs without ``jsonschema`` still
    surface gross structural problems.
    """
    path = schema_path or _VENDORED_SCHEMA
    if not path.exists():
        return [f"vendored schema not found at {path}"]

    with path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)

    declared = schema.get("schema_version")
    if declared and declared != schema_version:
        return [
            f"schema_version mismatch — vendored={declared}, requested={schema_version}"
        ]

    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft7Validator(schema)
        errors = [
            f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
            for err in validator.iter_errors(payload)
        ]
        return errors
    except ImportError:
        return _shallow_required_check(payload)


def _shallow_required_check(payload: dict[str, Any]) -> list[str]:
    """Minimal fallback when ``jsonschema`` is not installed."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"missing required top-level key: {key}")
    handoff = payload.get("aaa_phase5_handoff", {})
    for key in (
        "phase5_verdict", "phase5_narrative_summary", "blocking_findings_count",
        "blocking_findings", "positive_findings", "low_confidence_controls",
        "aaa_recommended_follow_up",
    ):
        if key not in handoff:
            errors.append(f"missing required aaa_phase5_handoff key: {key}")
    return errors


def cgsa_ingest(
    payload: dict[str, Any],
    phase1_risk_tier: str | None = None,
    schema_version: str = "1.0.0",
    strict: bool = True,
) -> IngestResult:
    """
    Validate + ingest a CGSA payload.

    Parameters
    ----------
    payload:
        Parsed JSON object returned by ``cgsa_pull``.
    phase1_risk_tier:
        Optional verified risk_tier from Phase 1 used for the cross-check.
    schema_version:
        Pinned CGSA schema version (must match the vendored copy).
    strict:
        When True (default), validation errors raise ``CGSAIngestError``.
        When False, errors are returned on the ``IngestResult`` so the
        caller (e.g. GovernanceAgent) can decide to ``escalate_hitl``
        without crashing the pipeline.
    """
    errors = schema_validate(payload, schema_version=schema_version)
    if errors and strict:
        raise CGSAIngestError("schema_validation_failed", {"errors": errors})

    metadata = payload.get("metadata", {}) or {}
    scores = payload.get("overall_scores", {}) or {}
    handoff = payload.get("aaa_phase5_handoff", {}) or {}
    hard = payload.get("hard_constraint_results", {}) or {}
    domains = payload.get("domains", []) or []
    remediation = payload.get("remediation_roadmap", []) or []

    # ── Low-confidence aggregation (CGSA + extracted from domain controls) ──
    low_conf = list(handoff.get("low_confidence_controls", []) or [])
    seen_ids = {item.get("control_id") for item in low_conf}
    for dom in domains:
        for ctrl in dom.get("controls", []) or []:
            conf = ctrl.get("confidence")
            cid = ctrl.get("control_id")
            if (
                conf is not None
                and conf < _LOW_CONFIDENCE_THRESHOLD
                and cid not in seen_ids
            ):
                low_conf.append({
                    "control_id": cid,
                    "control_name": ctrl.get("control_name", ""),
                    "confidence": conf,
                    "flag_reason": (
                        f"CGSA extraction confidence {conf:.2f} below "
                        f"{_LOW_CONFIDENCE_THRESHOLD:.2f} threshold."
                    ),
                })
                seen_ids.add(cid)

    # ── Risk-tier cross-check (Phase 1 vs CGSA) ─────────────────────────────
    cgsa_risk_tier = metadata.get("risk_tier")
    risk_tier_match: bool | None = None
    if phase1_risk_tier is not None and cgsa_risk_tier is not None:
        risk_tier_match = (phase1_risk_tier == cgsa_risk_tier)

    # ── State delta (§5.4 hydration map) ────────────────────────────────────
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
        "cgsa_recommended_follow_up": list(
            handoff.get("aaa_recommended_follow_up", []) or []
        ),
        "cgsa_report_url": handoff.get("cgsa_report_url"),
        "cgsa_risk_tier_match": risk_tier_match,
        "harmonised_standards_applied": _infer_harmonised_standards(domains),
    }

    # ── CSP failure ⇒ Phase 5 FAIL gate (overrides cgsa_phase5_verdict if needed)
    if scores.get("csp_satisfiable") is False:
        state_delta["cgsa_phase5_verdict"] = "FAIL"

    # ── Remediation roadmap → AuditState.remediation_roadmap (typed shape) ──
    state_delta["remediation_roadmap"] = [
        {
            "rank": int(item.get("rank", idx + 1)),
            "control_id": item.get("control_id", ""),
            "gap_detail": item.get("priority_rationale") or item.get("action", ""),
            "gap_severity": item.get("gap_severity", "medium"),
            "recommended_action": item.get("action", ""),
            "target_date": None,
        }
        for idx, item in enumerate(remediation)
    ]

    logger.info(
        "cgsa_ingest: schema_errors=%d, low_confidence=%d, csp_satisfiable=%s, "
        "phase5_verdict=%s, risk_tier_match=%s",
        len(errors), len(low_conf), scores.get("csp_satisfiable"),
        state_delta["cgsa_phase5_verdict"], risk_tier_match,
    )

    return IngestResult(
        payload=payload,
        state_delta=state_delta,
        low_confidence_controls=low_conf,
        schema_errors=errors,
        schema_version=schema_version,
    )


def _infer_harmonised_standards(domains: list[dict[str, Any]]) -> bool:
    """
    Infer ``harmonised_standards_applied`` from CGSA controls.

    True when at least one control under domain D3 (Model Development and
    Testing) cites a recognised harmonised standard family in its
    ``source_frameworks`` array (e.g. ISO 42001).
    """
    harmonised = {"ISO 42001"}
    for dom in domains or []:
        if dom.get("domain_id") != "D3":
            continue
        for ctrl in dom.get("controls", []) or []:
            for fw in ctrl.get("source_frameworks", []) or []:
                if fw in harmonised:
                    return True
    return False
