"""
aaa.dagster.assets.phase1 — Dagster asset for Phase 1 (Scope & Declaration Verifier).

Depends on ``intake_validation`` asset output.
Runs ScopeAgent and materialises T02–T05 artefacts.
"""
import asyncio
from typing import Any

from dagster import AssetExecutionContext, MetadataValue, asset

from aaa.agents.tier1.phases.phase_runners import run_phase_1
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import PHASE_LATENCY_HISTOGRAM
import time


@asset(
    name="phase1_scope",
    group_name="audit_pipeline",
    description="Phase 1 — Scope / Declaration Verifier. Produces T02–T05.",
    required_resource_keys={"evidence_store"},
    deps=["intake_validation"],
)
def phase1_scope_asset(
    context: AssetExecutionContext,
    intake_validation: dict[str, Any],
) -> dict[str, Any]:
    """Run ScopeAgent for Phase 1 and return updated AuditState."""
    from aaa.agents.tier2.scope_agent import ScopeAgent

    store = context.resources.evidence_store
    eid = intake_validation["engagement_id"]
    state = dict(intake_validation)

    t0 = time.perf_counter()
    try:
        agent = ScopeAgent(evidence_store=store)
        state = asyncio.run(run_phase_1(agent, state))
    except Exception as exc:
        capture_error(exc, component="dagster", context={"engagement_id": eid, "phase": "P1"}, reraise=False)
        context.log.error("Phase 1 failed for %s: %s", eid, exc)
        raise
    finally:
        elapsed = time.perf_counter() - t0
        PHASE_LATENCY_HISTOGRAM.labels(phase="P1", engagement_id=eid).observe(elapsed)

    context.add_output_metadata({
        "engagement_id": MetadataValue.text(eid),
        "verified_risk_tier": MetadataValue.text(state.get("risk_tier", "")),
        "verified_modality": MetadataValue.text(state.get("modality", "")),
        "phase1_latency_s": MetadataValue.float(round(time.perf_counter() - t0, 2)),
        "artefacts_produced": MetadataValue.int(
            len([k for k in state.get("phase_artefacts", {}) if k.startswith("T0")])
        ),
    })
    return state
