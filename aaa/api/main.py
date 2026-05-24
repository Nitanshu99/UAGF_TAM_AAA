"""
aaa.api.main — Minimal FastAPI application for engagement CRUD (§14.5).

Run::

    uvicorn aaa.api.main:app --reload --port 8000

Endpoints
---------
GET  /healthz                    — liveness probe; returns {status, schema_version}
GET  /api/v1/engagements         — list all engagements (in-memory store for demo)
POST /api/v1/engagements         — create a new engagement
GET  /api/v1/engagements/{id}    — retrieve engagement by ID
GET  /api/v1/schema-version      — return pinned CGSA schema version

In production these endpoints are backed by Postgres (via SQLAlchemy + Alembic
migrations).  For the thesis demo they use an in-memory dict so the endpoint
works without Docker services running.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from aaa.settings import settings

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AAA — Autonomous AI Auditor API",
    version="0.1.0",
    description="Engagement CRUD + health / schema-version endpoints (§14.5).",
)

# In-memory engagement store (replaced by Postgres in production).
_ENGAGEMENTS: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Schema models
# ---------------------------------------------------------------------------


class EngagementCreate(BaseModel):
    """Request body for POST /api/v1/engagements."""

    engagement_id: str | None = Field(
        None, description="Optional slug/UUID; auto-generated if omitted."
    )
    provider_name: str = Field(..., description="AI system provider name.")
    system_name: str = Field(..., description="AI system name.")
    declared_risk_tier: str = Field(
        ..., description="high | limited | minimal | gpai"
    )
    cgsa_assessment_id: str | None = Field(
        None, description="Optional S4 CGSA assessment ID for Phase 5."
    )


class EngagementOut(BaseModel):
    """Engagement resource returned by the API."""

    engagement_id: str
    provider_name: str
    system_name: str
    declared_risk_tier: str
    cgsa_assessment_id: str | None
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/healthz", tags=["ops"])
def healthz() -> dict[str, str]:
    """Liveness probe — returns {status, schema_version, offline_mode}."""
    return {
        "status": "ok",
        "schema_version": settings.cgsa_schema_version,
        "offline_mode": str(settings.is_offline()),
    }


@app.get("/api/v1/schema-version", tags=["schema"])
def schema_version() -> dict[str, str]:
    """Return the pinned CGSA schema version (§10.2)."""
    return {"cgsa_schema_version": settings.cgsa_schema_version}


@app.get("/api/v1/engagements", tags=["engagements"])
def list_engagements() -> list[dict[str, Any]]:
    """List all engagements (sorted newest-first)."""
    return sorted(
        _ENGAGEMENTS.values(),
        key=lambda e: e["created_at"],
        reverse=True,
    )


@app.post(
    "/api/v1/engagements",
    status_code=status.HTTP_201_CREATED,
    tags=["engagements"],
)
def create_engagement(body: EngagementCreate) -> JSONResponse:
    """Create a new engagement and return the resource."""
    eid = body.engagement_id or str(uuid.uuid4())
    if eid in _ENGAGEMENTS:
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
    _ENGAGEMENTS[eid] = record
    return JSONResponse(content=record, status_code=status.HTTP_201_CREATED)


@app.get("/api/v1/engagements/{engagement_id}", tags=["engagements"])
def get_engagement(engagement_id: str) -> dict[str, Any]:
    """Retrieve an engagement by ID."""
    record = _ENGAGEMENTS.get(engagement_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engagement '{engagement_id}' not found.",
        )
    return record
