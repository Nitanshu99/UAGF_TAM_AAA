"""``cgsa_ingest`` — validate a CGSA payload and derive the Phase 5 state delta.

Translates the S5 dialect first when the payload declares it, validates against
the pinned schema, then assembles the low-confidence list, the risk-tier
cross-check and the state delta the GovernanceAgent applies.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.aggregate_low_confidence import _aggregate_low_confidence
from aaa.tools.cgsa_ingest.build_state_delta import _build_state_delta
from aaa.tools.cgsa_ingest.logger import CGSAIngestError, IngestResult, logger
from aaa.tools.cgsa_ingest.risk_tier_match import _risk_tier_match
from aaa.tools.cgsa_ingest.s5.dialect import adapt_s5_dialect, is_s5_dialect
from aaa.tools.cgsa_ingest.schema_validate import schema_validate


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
    # Before validation, not after: S5 ships its own dialect, and a payload that
    # fails 339 checks makes the GovernanceAgent escalate before it reads a
    # control. The translation is a restatement of what S5 sent, so validating
    # the adapted payload is validating the same assessment (see .s5_dialect).
    if is_s5_dialect(payload):
        payload = adapt_s5_dialect(payload)

    errors = schema_validate(payload, schema_version=schema_version)
    if errors and strict:
        raise CGSAIngestError("schema_validation_failed", {"errors": errors})

    metadata = payload.get("metadata", {}) or {}
    scores = payload.get("overall_scores", {}) or {}
    handoff = payload.get("aaa_phase5_handoff", {}) or {}
    domains = payload.get("domains", []) or []
    remediation = payload.get("remediation_roadmap", []) or []

    low_conf = _aggregate_low_confidence(handoff, domains)

    risk_tier_match = _risk_tier_match(phase1_risk_tier, metadata.get("risk_tier"))

    state_delta = _build_state_delta(payload, schema_version, scores, handoff,
                                     domains, remediation, low_conf, risk_tier_match)

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
