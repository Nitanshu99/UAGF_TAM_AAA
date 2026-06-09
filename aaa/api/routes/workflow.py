"""
aaa.api.routes.workflow — Customer-facing engagement workflow endpoints.

Endpoints
---------
POST /api/v1/engagements/{id}/files          — upload a file
POST /api/v1/engagements/{id}/intake         — submit Stage A/B/C payload
POST /api/v1/engagements/{id}/run            — run IntakeValidator → Orchestrator
POST /api/v1/engagements/{id}/extract-triage — DocIntelligenceAgent pre-fill
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from aaa.agents.base import IntakeDispatch
from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError
from aaa.agents.tier1.orchestrator import Orchestrator
from aaa.api.schemas import IntakePayload
from aaa.api.store import ENGAGEMENTS, INTAKE_PAYLOADS, FINAL_STATES, get_store
from aaa.data.models import UploadedFileMeta
from aaa.data.writer import save_intake, save_result, save_uploaded_file
from aaa.observability.error_handler import capture_error
from aaa.observability.metrics import ENGAGEMENT_COUNTER

router = APIRouter(prefix="/api/v1/engagements", tags=["customer-workflow"])


@router.post("/{engagement_id}/files", summary="Upload customer file")
async def upload_file(
    engagement_id: str,
    role: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Store a customer-uploaded artefact and return its EvidenceStore URI."""
    if engagement_id not in ENGAGEMENTS:
        raise HTTPException(status_code=404, detail=f"Engagement '{engagement_id}' not found.")
    data = await file.read()
    store = get_store(engagement_id)
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

    # ── Persist file metadata ──────────────────────────────────────────────
    save_uploaded_file(UploadedFileMeta(
        engagement_id=engagement_id,
        filename=file.filename or "upload.bin",
        role=role,
        content_type=file.content_type or "application/octet-stream",
        bytes_size=len(data),
        sha256=payload.get("sha256", ""),
        uri=uri,
    ))

    return {"uri": uri, "sha256": payload.get("sha256", ""), "role": role}


@router.post("/{engagement_id}/intake", summary="Submit intake payload")
def submit_intake(engagement_id: str, body: IntakePayload) -> dict[str, Any]:
    """Submit Stage A/B/C payloads whose URI fields reference uploaded files."""
    if engagement_id not in ENGAGEMENTS:
        raise HTTPException(status_code=404, detail=f"Engagement '{engagement_id}' not found.")
    dumped = body.model_dump()
    INTAKE_PAYLOADS[engagement_id] = dumped
    ENGAGEMENTS[engagement_id]["status"] = "intake_submitted"

    # ── Persist intake payload ─────────────────────────────────────────────
    save_intake(
        engagement_id=engagement_id,
        stage_a=dumped.get("stage_a", {}),
        stage_b=dumped.get("stage_b", {}),
        stage_c=dumped.get("stage_c"),
    )

    return {"engagement_id": engagement_id, "status": "intake_submitted"}


@router.post("/{engagement_id}/run", summary="Run full audit pipeline")
async def run_engagement(engagement_id: str) -> dict[str, Any]:
    """Run IntakeValidator → Orchestrator for the submitted engagement."""
    payload = INTAKE_PAYLOADS.get(engagement_id)
    if payload is None:
        raise HTTPException(status_code=400, detail="Intake payload not submitted.")
    store = get_store(engagement_id)
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
        ENGAGEMENTS[engagement_id]["status"] = "intake_failed"
        ENGAGEMENT_COUNTER.labels(status="intake_failed", final_verdict="N/A").inc()
        capture_error(exc, component="api", context={"engagement_id": engagement_id}, reraise=False)
        raise HTTPException(status_code=400, detail={"stage": exc.stage, "reason": exc.reason})
    final = await Orchestrator(evidence_store=store).run(dict(initial))
    if final.get("final_verdict") is None:
        final["final_verdict"] = "FAIL"
    FINAL_STATES[engagement_id] = final
    ENGAGEMENTS[engagement_id]["status"] = "completed"
    ENGAGEMENT_COUNTER.labels(status="completed", final_verdict=final["final_verdict"]).inc()

    # ── Persist audit result ───────────────────────────────────────────────
    save_result(engagement_id, final)

    return {
        "engagement_id": engagement_id,
        "status": "completed",
        "final_verdict": final.get("final_verdict"),
        "regulatory_coverage_pct": final.get("regulatory_coverage_pct"),
    }


@router.post("/{engagement_id}/extract-triage", summary="AI pre-fill from uploaded docs")
async def extract_triage(engagement_id: str) -> dict[str, Any]:
    """Run DocIntelligenceAgent over uploaded files and return pre-filled Stage A/B fields."""
    if engagement_id not in ENGAGEMENTS:
        raise HTTPException(status_code=404, detail=f"Engagement '{engagement_id}' not found.")
    from aaa.agents.doc_intelligence import DocIntelligenceAgent
    store = get_store(engagement_id)
    doc_uris = [
        uri
        for uri, meta in store._store.items()  # type: ignore[attr-defined]
        if isinstance(meta, dict) and meta.get("engagement_id") == engagement_id
        and meta.get("phase") == "customer_uploads"
    ]
    agent = DocIntelligenceAgent(evidence_store=store)
    result = await agent.process({"engagement_id": engagement_id, "doc_uris": doc_uris})
    return dict(result)
