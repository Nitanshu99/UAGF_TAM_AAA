"""aaa.dagster.assets.phase2 — Phase 2 Data Governance Auditor asset."""
import asyncio, time
from typing import Any
from dagster import AssetExecutionContext, MetadataValue, asset
from aaa.agents.tier1.phases.phase_runners import run_phase_2
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import PHASE_LATENCY_HISTOGRAM


@asset(
    name="phase2_data",
    group_name="audit_pipeline",
    description="Phase 2 — Data Governance Auditor. Produces T06–T08.",
    required_resource_keys={"evidence_store"},
    deps=["phase1_scope"],
)
def phase2_data_asset(
    context: AssetExecutionContext,
    phase1_scope: dict[str, Any],
) -> dict[str, Any]:
    """Run DataAuditor for Phase 2."""
    from aaa.agents.tier2.data_auditor import DataAuditor

    store = context.resources.evidence_store
    eid = phase1_scope["engagement_id"]
    state = dict(phase1_scope)
    t0 = time.perf_counter()
    try:
        state = asyncio.run(run_phase_2(DataAuditor(evidence_store=store), state))
    except Exception as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid, "phase": "P2"}, reraise=False)
        context.log.error("Phase 2 failed: %s", exc)
        raise
    finally:
        PHASE_LATENCY_HISTOGRAM.labels(phase="P2", engagement_id=eid).observe(time.perf_counter() - t0)
    context.add_output_metadata({"engagement_id": MetadataValue.text(eid)})
    return state
