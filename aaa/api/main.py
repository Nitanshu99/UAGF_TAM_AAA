"""
aaa.api.main — FastAPI application factory (§14.5).

Run::

    uvicorn aaa.api.main:app --reload --port 8000

All route logic has been moved to ``aaa.api.routes.*`` sub-modules.
This file is intentionally thin — it only wires routers and configures
middleware / lifespan hooks.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from aaa.api.routes.health import router as health_router
from aaa.api.routes.engagements import router as engagements_router
from aaa.api.routes.workflow import router as workflow_router
from aaa.api.routes.reports import router as reports_router
from aaa.api.routes.data import router as data_router
from aaa.observability.logging_config import configure_logging


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Configure logging on startup."""
    configure_logging()
    yield


app = FastAPI(
    title="AAA — Autonomous AI Auditor API",
    version="0.1.0",
    description=(
        "Engagement CRUD, health probes, Prometheus metrics, "
        "and full audit workflow endpoints (§14.5)."
    ),
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(engagements_router)
app.include_router(workflow_router)
app.include_router(reports_router)
app.include_router(data_router)
