"""aaa.dagster.assets.phase4 — Phase 4 Output Fairness Tester asset."""
import asyncio, time
from typing import Any
from dagster import AssetExecutionContext, MetadataValue, asset
from aaa.agents.tier1.phases.phase_runners import run_phase_4
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import PHASE_LATENCY_HISTOGRAM


@asset(
    name="phase4_fairness",
    group_name="audit_pipeline",
    description="Phase 4 — Output Fairness Tester. Produces T12–T13.",
    required_resource_keys={"evidence_store"},
    deps=["phase3_model"],
)
def phase4_fairness_asset(
    context: AssetExecutionContext,
    phase3_model: dict[str, Any],
) -> dict[str, Any]:
    """Run OutputFairnessTester for Phase 4."""
    from aaa.agents.tier2.output_fairness import OutputFairnessTester

    store = context.resources.evidence_store
    eid = phase3_model["engagement_id"]
    state = dict(phase3_model)
    t0 = time.perf_counter()
    try:
        state = asyncio.run(run_phase_4(OutputFairnessTester(evidence_store=store), state))
    except Exception as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid, "phase": "P4"}, reraise=False)
        context.log.error("Phase 4 failed: %s", exc)
        raise
    finally:
        PHASE_LATENCY_HISTOGRAM.labels(phase="P4", engagement_id=eid).observe(time.perf_counter() - t0)
    context.add_output_metadata({"engagement_id": MetadataValue.text(eid)})
    return state
