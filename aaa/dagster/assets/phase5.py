"""aaa.dagster.assets.phase5 — Phase 5 Governance Agent asset."""
from __future__ import annotations
import asyncio, time
from typing import Any
from dagster import AssetExecutionContext, MetadataValue, asset
from aaa.agents.tier1.phases.phase_runners import run_phase_5
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import PHASE_LATENCY_HISTOGRAM


@asset(
    name="phase5_governance",
    group_name="audit_pipeline",
    description="Phase 5 — Governance Agent. Pulls CGSA, produces T14–T15.",
    required_resource_keys={"evidence_store"},
    deps=["phase4_fairness"],
)
def phase5_governance_asset(
    context: AssetExecutionContext,
    phase4_fairness: dict[str, Any],
) -> dict[str, Any]:
    """Run GovernanceAgent for Phase 5 (S4 CGSA integration)."""
    from aaa.agents.tier2.governance_agent import GovernanceAgent

    store = context.resources.evidence_store
    eid = phase4_fairness["engagement_id"]
    state = dict(phase4_fairness)
    t0 = time.perf_counter()
    try:
        state = asyncio.run(run_phase_5(GovernanceAgent(evidence_store=store), state))
    except Exception as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid, "phase": "P5"}, reraise=False)
        context.log.error("Phase 5 failed: %s", exc)
        raise
    finally:
        PHASE_LATENCY_HISTOGRAM.labels(phase="P5", engagement_id=eid).observe(time.perf_counter() - t0)
    context.add_output_metadata({
        "engagement_id": MetadataValue.text(eid),
        "cgsa_phase5_verdict": MetadataValue.text(str(state.get("cgsa_phase5_verdict") or "N/A")),
    })
    return state
