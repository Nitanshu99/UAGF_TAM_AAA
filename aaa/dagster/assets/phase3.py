"""aaa.dagster.assets.phase3 — Phase 3 Model Validator asset."""
from __future__ import annotations
import asyncio, time
from typing import Any
from dagster import AssetExecutionContext, MetadataValue, asset
from aaa.agents.tier1.phases.phase_runners import run_phase_3
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import PHASE_LATENCY_HISTOGRAM


@asset(
    name="phase3_model",
    group_name="audit_pipeline",
    description="Phase 3 — Model Validator. Produces T09–T11.",
    required_resource_keys={"evidence_store"},
    deps=["phase2_data"],
)
def phase3_model_asset(
    context: AssetExecutionContext,
    phase2_data: dict[str, Any],
) -> dict[str, Any]:
    """Run ModelValidator for Phase 3."""
    from aaa.agents.tier2.model_validator import ModelValidator

    store = context.resources.evidence_store
    eid = phase2_data["engagement_id"]
    state = dict(phase2_data)
    t0 = time.perf_counter()
    try:
        state = asyncio.run(run_phase_3(ModelValidator(evidence_store=store), state))
    except Exception as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid, "phase": "P3"}, reraise=False)
        context.log.error("Phase 3 failed: %s", exc)
        raise
    finally:
        PHASE_LATENCY_HISTOGRAM.labels(phase="P3", engagement_id=eid).observe(time.perf_counter() - t0)
    context.add_output_metadata({"engagement_id": MetadataValue.text(eid)})
    return state
