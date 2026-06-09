"""
aaa.dagster.assets.phase6 — Phase 6 Report Architect asset + compliance matrix.

This is the terminal phase asset.  It:
1. Runs node_compliance_matrix to assemble the final verdict.
2. Runs ReportArchitect to produce T17/T18.
3. Surfaces key KPIs as Dagster metadata.
"""
from __future__ import annotations
import asyncio, time
from typing import Any
from dagster import AssetExecutionContext, MetadataValue, asset
from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.phase_runners import run_phase_6
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import PHASE_LATENCY_HISTOGRAM, ENGAGEMENT_COUNTER


@asset(
    name="phase6_report",
    group_name="audit_pipeline",
    description="Phase 6 — Compliance matrix + Report Architect. Produces T17–T18.",
    required_resource_keys={"evidence_store"},
    deps=["phase5_governance"],
)
def phase6_report_asset(
    context: AssetExecutionContext,
    phase5_governance: dict[str, Any],
) -> dict[str, Any]:
    """Assemble compliance matrix and produce final audit report."""
    from aaa.agents.tier2.report_architect import ReportArchitect

    store = context.resources.evidence_store
    eid = phase5_governance["engagement_id"]
    state = dict(phase5_governance)
    t0 = time.perf_counter()

    try:
        # Step 1: compliance matrix + final verdict
        state = node_compliance_matrix(state)
        # Step 2: generate T17/T18
        state = asyncio.run(run_phase_6(ReportArchitect(evidence_store=store), state))
    except Exception as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid, "phase": "P6"}, reraise=False)
        context.log.error("Phase 6 failed: %s", exc)
        raise
    finally:
        PHASE_LATENCY_HISTOGRAM.labels(phase="P6", engagement_id=eid).observe(time.perf_counter() - t0)

    verdict = state.get("final_verdict") or "FAIL"
    ENGAGEMENT_COUNTER.labels(status="completed", final_verdict=verdict).inc()

    context.add_output_metadata({
        "engagement_id": MetadataValue.text(eid),
        "final_verdict": MetadataValue.text(verdict),
        "completeness_score": MetadataValue.float(state.get("completeness_score") or 0.0),
        "regulatory_coverage_pct": MetadataValue.float(
            state.get("regulatory_coverage_pct") or 0.0
        ),
        "material_findings": MetadataValue.int(state.get("material_findings_count") or 0),
    })
    return state
