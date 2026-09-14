"""Completion bookkeeping for the pipeline-run endpoint."""
from __future__ import annotations

from typing import Any

from aaa.api.store import ENGAGEMENTS, FINAL_STATES
from aaa.data.writer import save_customer_artefacts, save_result
from aaa.observability.metrics import ENGAGEMENT_COUNTER
from aaa.platform.evidence import EvidenceStore
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION


def record_completion(engagement_id: str, final: dict[str, Any],
                      store: EvidenceStore, full: bool) -> dict[str, Any]:
    """Persist the final state and build the /run response payload.

    :param engagement_id: Engagement identifier.
    :param final: Final audit state from the Orchestrator.
    :param store: Evidence store for the engagement.
    :param full: When true, include the complete audit state inline.
    :returns: The /run endpoint response body.
    """
    # A run that produced no verdict could not conclude; recording FAIL here
    # asserted a non-conformity nobody established (F11).
    if final.get("final_verdict") is None:
        final["final_verdict"] = DISCLAIMER_OF_OPINION
    FINAL_STATES[engagement_id] = final
    ENGAGEMENTS[engagement_id]["status"] = "completed"
    ENGAGEMENT_COUNTER.labels(status="completed",
                              final_verdict=final["final_verdict"]).inc()
    save_result(engagement_id, final)
    # Per-company deliverables: audit_state + T17 + T18 under data/customer/<company>/
    save_customer_artefacts(engagement_id, final, store)
    response: dict[str, Any] = {
        "engagement_id": engagement_id,
        "status": "completed",
        "final_verdict": final.get("final_verdict"),
        "regulatory_coverage_pct": final.get("regulatory_coverage_pct"),
    }
    if full:
        response["audit_state"] = final
    return response
