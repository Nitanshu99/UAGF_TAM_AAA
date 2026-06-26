"""
aaa.dagster.assets.intake — Dagster asset for Stage 0 intake validation.

Runs IntakeValidator and materialises the validated AuditState dict.
Metadata surfaced: completeness score, art43 preview, stage gate result.
"""
import asyncio
from typing import Any

from dagster import AssetExecutionContext, MetadataValue, asset

from aaa.observability.logging_config import configure_logging
from aaa.observability.error_handler import capture_error

configure_logging()


def _load_engagement_payload(engagement_id: str) -> dict[str, Any]:
    """Load the submitted intake payload for an engagement."""
    from aaa.api.store import INTAKE_PAYLOADS
    from aaa.data.reader import load_intake

    payload = INTAKE_PAYLOADS.get(engagement_id) or load_intake(engagement_id)
    if payload is None:
        raise FileNotFoundError(
            f"No intake payload found for engagement_id={engagement_id!r}. "
            "Submit intake first or provide a valid engagement_id."
        )
    return {"engagement_id": engagement_id, **payload}


@asset(
    name="intake_validation",
    group_name="audit_pipeline",
    description="Stage 0 — validate intake bundle (A/B/C) via IntakeValidator.",
    config_schema={"engagement_id": str},
    required_resource_keys={"evidence_store"},
)
def intake_validation_asset(
    context: AssetExecutionContext,
) -> dict[str, Any]:
    """Run IntakeValidator and return the initial AuditState.

    Parameters
    ----------
    context:
        Dagster execution context (provides resources, logging).

    Returns
    -------
    dict — the initial AuditState ready for Phase 1.
    """
    from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError
    from aaa.agents.base import IntakeDispatch

    store = context.resources.evidence_store
    eid = context.op_execution_context.op_config["engagement_id"]
    engagement_payload = _load_engagement_payload(eid)

    stage_a_uri = store.store_artefact(eid, "stage_a_raw", "stage_a_raw",
                                       engagement_payload["stage_a"], "dagster")
    stage_b_uri = store.store_artefact(eid, "stage_b_raw", "stage_b_raw",
                                       engagement_payload["stage_b"], "dagster")
    stage_c = engagement_payload.get("stage_c")
    stage_c_uri = (
        store.store_artefact(eid, "stage_c_raw", "stage_c_raw", stage_c, "dagster")
        if stage_c is not None else None
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
            float(state.get("intake_completeness_score") or 0.0)
        ),
        "declared_risk_tier": MetadataValue.text(state.get("declared_risk_tier", "")),
        "art43_preview": MetadataValue.text(
            str(state.get("art43_decision") or "pending")
        ),
    })
    return dict(state)
