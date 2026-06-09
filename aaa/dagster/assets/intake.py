"""
aaa.dagster.assets.intake — Dagster asset for Stage 0 intake validation.

Runs IntakeValidator and materialises the validated AuditState dict.
Metadata surfaced: completeness score, art43 preview, stage gate result.
"""
from __future__ import annotations

import asyncio
from typing import Any

from dagster import AssetExecutionContext, MetadataValue, asset

from aaa.observability.logging_config import configure_logging
from aaa.observability.error_handler import capture_error

configure_logging()


@asset(
    name="intake_validation",
    group_name="audit_pipeline",
    description="Stage 0 — validate intake bundle (A/B/C) via IntakeValidator.",
    required_resource_keys={"evidence_store"},
)
def intake_validation_asset(
    context: AssetExecutionContext,
    engagement_payload: dict[str, Any],
) -> dict[str, Any]:
    """Run IntakeValidator and return the initial AuditState.

    Parameters
    ----------
    context:
        Dagster execution context (provides resources, logging).
    engagement_payload:
        Dict with keys ``engagement_id``, ``stage_a``, ``stage_b``,
        and optionally ``stage_c``.

    Returns
    -------
    dict — the initial AuditState ready for Phase 1.
    """
    from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError
    from aaa.agents.base import IntakeDispatch

    store = context.resources.evidence_store
    eid = engagement_payload["engagement_id"]

    stage_a_uri = store.store_artefact(eid, "stage_a_raw", "stage_a_raw",
                                       engagement_payload["stage_a"], "dagster")
    stage_b_uri = store.store_artefact(eid, "stage_b_raw", "stage_b_raw",
                                       engagement_payload["stage_b"], "dagster")
    stage_c = engagement_payload.get("stage_c")
    stage_c_uri = (
        store.store_artefact(eid, "stage_c_raw", "stage_c_raw", stage_c, "dagster")
        if stage_c else None
    )

    dispatch: IntakeDispatch = {
        "engagement_id": eid,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }

    try:
        state = asyncio.run(IntakeValidator(evidence_store=store).process(dispatch))
    except IntakeValidatorError as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid}, reraise=False)
        context.log.error("IntakeValidator failed: stage=%s reason=%s", exc.stage, exc.reason)
        raise

    context.add_output_metadata({
        "engagement_id": MetadataValue.text(eid),
        "intake_completeness_score": MetadataValue.float(
            state.get("intake_completeness_score") or 0.0
        ),
        "declared_risk_tier": MetadataValue.text(state.get("declared_risk_tier", "")),
        "art43_preview": MetadataValue.text(
            str(state.get("art43_decision") or "pending")
        ),
    })
    return dict(state)
