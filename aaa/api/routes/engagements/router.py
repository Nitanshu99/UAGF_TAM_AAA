"""Part 1 of the former ``engagements`` module (auto-split)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from aaa.api.schemas import EngagementCreate
from aaa.api.store import ENGAGEMENTS, get_store
from aaa.data.models import EngagementRecord
from aaa.data.writer import save_engagement

router = APIRouter(prefix="/api/v1/engagements", tags=["engagements"])


@router.get("", summary="List all engagements")
def list_engagements() -> list[dict[str, Any]]:
    """List all engagements sorted newest-first."""
    return sorted(
        ENGAGEMENTS.values(),
        key=lambda e: e["created_at"],
        reverse=True,
    )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create engagement")
def create_engagement(body: EngagementCreate) -> JSONResponse:
    """Create a new engagement and return the resource."""
    eid = body.engagement_id or str(uuid.uuid4())
    if eid in ENGAGEMENTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Engagement '{eid}' already exists.",
        )
    record: dict[str, Any] = {
        "engagement_id": eid,
        "provider_name": body.provider_name,
        "system_name": body.system_name,
        "declared_risk_tier": body.declared_risk_tier,
        "cgsa_assessment_id": body.cgsa_assessment_id,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ENGAGEMENTS[eid] = record
    get_store(eid)  # initialise EvidenceStore eagerly

    # ── Persist to data/ folder ────────────────────────────────────────────
    save_engagement(EngagementRecord(
        engagement_id=eid,
        provider_name=body.provider_name,
        system_name=body.system_name,
        declared_risk_tier=body.declared_risk_tier,
        cgsa_assessment_id=body.cgsa_assessment_id,
        status="created",
        created_at=record["created_at"],
    ))

    return JSONResponse(content=record, status_code=status.HTTP_201_CREATED)
