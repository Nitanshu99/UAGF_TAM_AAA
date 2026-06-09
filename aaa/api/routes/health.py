"""
aaa.api.routes.health — Liveness / readiness probes and Prometheus metrics.

Endpoints
---------
GET  /healthz          — liveness probe
GET  /api/v1/schema-version — pinned CGSA schema version
GET  /metrics          — Prometheus text exposition
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from aaa.settings import settings

router = APIRouter()


@router.get("/healthz", tags=["ops"])
def healthz() -> dict[str, str]:
    """Liveness probe — returns {status, schema_version, offline_mode}."""
    return {
        "status": "ok",
        "schema_version": settings.cgsa_schema_version,
        "offline_mode": str(settings.is_offline()),
    }


@router.get("/api/v1/schema-version", tags=["schema"])
def schema_version() -> dict[str, str]:
    """Return the pinned CGSA schema version (§10.2)."""
    return {"cgsa_schema_version": settings.cgsa_schema_version}


@router.get("/metrics", tags=["ops"], response_class=PlainTextResponse)
def prometheus_metrics() -> PlainTextResponse:
    """Expose Prometheus metrics for scraping."""
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
