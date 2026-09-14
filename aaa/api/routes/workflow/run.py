"""Pipeline-run endpoint: IntakeValidator → Orchestrator."""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import HTTPException

from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError
from aaa.agents.tier1.orchestrator import Orchestrator
from aaa.agents.tier1.regulatory_rag import build_regulatory_rag
from aaa.api.routes.workflow.base import router
from aaa.api.routes.workflow.dispatch import build_dispatch
from aaa.api.routes.workflow.finish import record_completion
from aaa.api.store import ENGAGEMENTS, INTAKE_PAYLOADS, get_store
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import ENGAGEMENT_COUNTER

logger = logging.getLogger(__name__)


@router.post("/{engagement_id}/run", summary="Run full audit pipeline")
async def run_engagement(engagement_id: str, full: bool = False) -> dict[str, Any]:
    """Run IntakeValidator → Orchestrator for the submitted engagement.

    :param engagement_id: Engagement to run.
    :param full: When true, include the complete final audit state inline.
    :returns: Verdict summary, plus ``audit_state`` when *full* is set.
    :raises fastapi.HTTPException: 400 when intake is missing or rejected.
    """
    payload = INTAKE_PAYLOADS.get(engagement_id)
    if payload is None:
        raise HTTPException(status_code=400, detail="Intake payload not submitted.")
    store = get_store(engagement_id)
    dispatch = build_dispatch(store, engagement_id, payload)
    logger.info("[%s] run started: dispatching IntakeValidator", engagement_id)
    t_intake = time.monotonic()
    try:
        initial = await IntakeValidator(evidence_store=store).process(dispatch)
    except IntakeValidatorError as exc:
        ENGAGEMENTS[engagement_id]["status"] = "intake_failed"
        ENGAGEMENT_COUNTER.labels(status="intake_failed", final_verdict="N/A").inc()
        capture_error(exc, component="api",
                      context={"engagement_id": engagement_id}, reraise=False)
        raise HTTPException(status_code=400,
                            detail={"stage": exc.stage, "reason": exc.reason}) from exc
    logger.info("[%s] IntakeValidator complete in %.1fs; dispatching Orchestrator",
                engagement_id, time.monotonic() - t_intake)
    t_orch = time.monotonic()
    final = await Orchestrator(evidence_store=store,
                               regulatory_rag=build_regulatory_rag(),
                               ).run(dict(initial))
    logger.info("[%s] Orchestrator complete in %.1fs",
                engagement_id, time.monotonic() - t_orch)
    return record_completion(engagement_id, final, store, full)
