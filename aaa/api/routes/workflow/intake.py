"""Intake-submission endpoint."""
from __future__ import annotations

from typing import Any

from aaa.api.routes.workflow.base import require_engagement, router
from aaa.api.schemas import IntakePayload
from aaa.api.store import ENGAGEMENTS, INTAKE_PAYLOADS
from aaa.data.writer import save_intake


@router.post("/{engagement_id}/intake", summary="Submit intake payload")
def submit_intake(engagement_id: str, body: IntakePayload) -> dict[str, Any]:
    """Submit Stage A/B/C payloads whose URI fields reference uploaded files.

    :param engagement_id: Engagement the intake belongs to.
    :param body: Stage A/B/C intake payload.
    :returns: ``{engagement_id, status}`` acknowledgement.
    """
    require_engagement(engagement_id)
    dumped = body.model_dump()
    INTAKE_PAYLOADS[engagement_id] = dumped
    ENGAGEMENTS[engagement_id]["status"] = "intake_submitted"
    save_intake(
        engagement_id=engagement_id,
        stage_a=dumped.get("stage_a", {}),
        stage_b=dumped.get("stage_b", {}),
        stage_c=dumped.get("stage_c"),
    )
    return {"engagement_id": engagement_id, "status": "intake_submitted"}
