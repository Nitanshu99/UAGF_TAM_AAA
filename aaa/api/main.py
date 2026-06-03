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

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from aaa.agents.base import IntakeDispatch
from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError
from aaa.agents.tier1.orchestrator import Orchestrator
from aaa.platform.evidence import EvidenceStore
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
_STORES: dict[str, EvidenceStore] = {}
_INTAKE_PAYLOADS: dict[str, dict[str, Any]] = {}
_FINAL_STATES: dict[str, dict[str, Any]] = {}

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


class IntakePayload(BaseModel):
    """Stage A/B/C payload submission for an engagement."""

    stage_a: dict[str, Any]
    stage_b: dict[str, Any]
    stage_c: dict[str, Any] | None = None


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
    _STORES[eid] = EvidenceStore()
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


@app.post("/api/v1/engagements/{engagement_id}/files", tags=["customer-workflow"])
async def upload_file(
    engagement_id: str,
    role: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Store a customer-uploaded artefact and return its EvidenceStore URI."""
    if engagement_id not in _ENGAGEMENTS:
        raise HTTPException(status_code=404, detail=f"Engagement '{engagement_id}' not found.")
    data = await file.read()
    store = _STORES.setdefault(engagement_id, EvidenceStore())
    uri = store.store_file(
        engagement_id=engagement_id,
        phase="customer_uploads",
        artefact_type=role,
        filename=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        agent_name="api",
    )
    payload = store.get_artefact(uri) or {}
    return {"uri": uri, "sha256": payload.get("sha256", ""), "role": role}


@app.post("/api/v1/engagements/{engagement_id}/intake", tags=["customer-workflow"])
def submit_intake(engagement_id: str, body: IntakePayload) -> dict[str, Any]:
    """Submit Stage A/B/C payloads whose URI fields reference uploaded files."""
    if engagement_id not in _ENGAGEMENTS:
        raise HTTPException(status_code=404, detail=f"Engagement '{engagement_id}' not found.")
    _INTAKE_PAYLOADS[engagement_id] = body.model_dump()
    _ENGAGEMENTS[engagement_id]["status"] = "intake_submitted"
    return {"engagement_id": engagement_id, "status": "intake_submitted"}


@app.post("/api/v1/engagements/{engagement_id}/run", tags=["customer-workflow"])
async def run_engagement(engagement_id: str) -> dict[str, Any]:
    """Run IntakeValidator → Orchestrator for the submitted engagement."""
    payload = _INTAKE_PAYLOADS.get(engagement_id)
    if payload is None:
        raise HTTPException(status_code=400, detail="Intake payload not submitted.")
    store = _STORES.setdefault(engagement_id, EvidenceStore())
    stage_a_uri = store.store_artefact(
        engagement_id, "stage_a_raw", "stage_a_raw", payload["stage_a"], "api")
    stage_b_uri = store.store_artefact(
        engagement_id, "stage_b_raw", "stage_b_raw", payload["stage_b"], "api")
    stage_c = payload.get("stage_c")
    stage_c_uri = (
        store.store_artefact(engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "api")
        if stage_c is not None else None
    )
    dispatch: IntakeDispatch = {
        "engagement_id": engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }
    try:
        initial = await IntakeValidator(evidence_store=store).process(dispatch)
    except IntakeValidatorError as exc:
        _ENGAGEMENTS[engagement_id]["status"] = "intake_failed"
        raise HTTPException(status_code=400, detail={"stage": exc.stage, "reason": exc.reason})
    final = await Orchestrator(evidence_store=store).run(dict(initial))
    if final.get("final_verdict") is None:
        final["final_verdict"] = "FAIL"
    _FINAL_STATES[engagement_id] = final
    _ENGAGEMENTS[engagement_id]["status"] = "completed"
    return {
        "engagement_id": engagement_id,
        "status": "completed",
        "final_verdict": final.get("final_verdict"),
        "regulatory_coverage_pct": final.get("regulatory_coverage_pct"),
    }


@app.post("/api/v1/engagements/{engagement_id}/extract-triage", tags=["customer-workflow"])
async def extract_triage(engagement_id: str) -> dict[str, Any]:
    """Run DocIntelligenceAgent over uploaded files and return pre-filled Stage A/B fields."""
    if engagement_id not in _ENGAGEMENTS:
        raise HTTPException(status_code=404, detail=f"Engagement '{engagement_id}' not found.")
    from aaa.agents.doc_intelligence import DocIntelligenceAgent
    store = _STORES.setdefault(engagement_id, EvidenceStore())
    doc_uris = [
        uri
        for uri, meta in store._store.items()  # type: ignore[attr-defined]
        if isinstance(meta, dict) and meta.get("engagement_id") == engagement_id
        and meta.get("phase") == "customer_uploads"
    ]
    agent = DocIntelligenceAgent(evidence_store=store)
    result = await agent.process({"engagement_id": engagement_id, "doc_uris": doc_uris})
    return dict(result)


@app.get("/api/v1/engagements/{engagement_id}/report", tags=["customer-workflow"])
def get_report(engagement_id: str) -> dict[str, Any]:
    """Return final verdict, KPI summary, and report artefact URIs."""
    final = _FINAL_STATES.get(engagement_id)
    if final is None:
        raise HTTPException(status_code=404, detail="Report not available.")
    store = _STORES.setdefault(engagement_id, EvidenceStore())
    t18_uri = (final.get("phase_artefacts") or {}).get("T18_audit_report", {}).get("uri", "")
    t18 = store.get_artefact(t18_uri) or {}
    rendered = t18.get("rendered_report", {}) or {}
    return {
        "engagement_id": engagement_id,
        "final_verdict": final.get("final_verdict"),
        "kpis": {
            "intake_completeness_score": final.get("intake_completeness_score"),
            "completeness_score": final.get("completeness_score"),
            "regulatory_coverage_pct": final.get("regulatory_coverage_pct"),
        },
        "t18_json_uri": rendered.get("json_uri") or t18_uri,
        "pdf_uri": rendered.get("pdf_uri"),
    }


@app.get("/api/v1/engagements/{engagement_id}/report.pdf", tags=["customer-workflow"])
def get_report_pdf(engagement_id: str) -> Response:
    """Return rendered PDF bytes when ReportLab output is available."""
    report = get_report(engagement_id)
    store = _STORES.setdefault(engagement_id, EvidenceStore())
    payload = store.get_artefact(report.get("pdf_uri") or "") or {}
    if payload.get("encoding") != "latin-1":
        raise HTTPException(status_code=404, detail="Rendered PDF not available.")
    return Response(
        content=str(payload.get("body", "")).encode("latin-1"),
        media_type="application/pdf",
    )
