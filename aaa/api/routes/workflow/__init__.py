"""Customer-facing engagement workflow endpoints.

Endpoints
---------
- ``POST /api/v1/engagements/{id}/files`` — upload a file
- ``POST /api/v1/engagements/{id}/intake`` — submit Stage A/B/C payload
- ``POST /api/v1/engagements/{id}/run`` — run IntakeValidator → Orchestrator
- ``GET  /api/v1/engagements/{id}/audit-state`` — final audit-state JSON
- ``GET  /api/v1/engagements/{id}/hitl-review`` — HITL review packet
- ``POST /api/v1/engagements/{id}/extract-triage`` — AI pre-fill from docs
"""
from __future__ import annotations

# The endpoint modules register themselves on the shared router at import
# time, so they must be imported for their routes to exist.
from aaa.api.routes.workflow import extract, files, intake, run, state  # noqa: F401
from aaa.api.routes.workflow.base import router

__all__ = ["router"]
