"""
aaa.api.routes.data — REST endpoints for querying the file-based data store.

These endpoints let the user retrieve what they entered (inputs) and what the
audit produced (results) from the persistent ``data/`` folder.

Endpoints
---------
GET  /api/v1/data/engagements                     — index: all stored engagements
GET  /api/v1/data/engagements/{id}/input          — stored user inputs (engagement + intake + files)
GET  /api/v1/data/engagements/{id}/input/engagement  — engagement creation record
GET  /api/v1/data/engagements/{id}/input/intake      — Stage A/B/C payload
GET  /api/v1/data/engagements/{id}/input/files       — uploaded-file metadata list
GET  /api/v1/data/engagements/{id}/result         — full audit result (verdict + KPIs + artefacts + findings)
GET  /api/v1/data/engagements/{id}/result/summary — verdict + KPIs only
GET  /api/v1/data/engagements/{id}/result/findings   — blocking / positive findings
GET  /api/v1/data/engagements/{id}/result/compliance — compliance matrix
GET  /api/v1/data/results                         — index: only completed engagements
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aaa.data import reader

router = APIRouter(prefix="/api/v1/data", tags=["data-store"])


# ── Index queries ─────────────────────────────────────────────────────────────

@router.get("/engagements", summary="List all stored engagements")
def list_stored_engagements() -> list[dict[str, Any]]:
    """Return the master index: one summary row per stored engagement."""
    return reader.list_engagements()


@router.get("/results", summary="List completed engagements")
def list_stored_results() -> list[dict[str, Any]]:
    """Return index rows for engagements that have a final verdict."""
    return reader.list_results()


# ── Input endpoints ───────────────────────────────────────────────────────────

@router.get("/engagements/{engagement_id}/input", summary="All stored user inputs")
def get_input(engagement_id: str) -> dict[str, Any]:
    """Return all user-entered data: engagement metadata, intake payload, uploaded files."""
    engagement = reader.load_engagement(engagement_id)
    if engagement is None:
        raise HTTPException(
            status_code=404,
            detail=f"No stored input found for engagement '{engagement_id}'.",
        )
    return {
        "engagement_id": engagement_id,
        "engagement":    engagement,
        "intake":        reader.load_intake(engagement_id),
        "uploaded_files": reader.load_uploaded_files(engagement_id),
    }


@router.get("/engagements/{engagement_id}/input/engagement",
            summary="Engagement creation record")
def get_input_engagement(engagement_id: str) -> dict[str, Any]:
    """Return the stored engagement creation metadata."""
    data = reader.load_engagement(engagement_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Engagement input not found.")
    return data


@router.get("/engagements/{engagement_id}/input/intake",
            summary="Stage A/B/C intake payload")
def get_input_intake(engagement_id: str) -> dict[str, Any]:
    """Return the stored Stage A/B/C payload submitted by the user."""
    data = reader.load_intake(engagement_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Intake payload not found.")
    return data


@router.get("/engagements/{engagement_id}/input/files",
            summary="Uploaded-file metadata")
def get_input_files(engagement_id: str) -> list[dict[str, Any]]:
    """Return the metadata list for all files uploaded by the user."""
    return reader.load_uploaded_files(engagement_id)


# ── Result endpoints ──────────────────────────────────────────────────────────

@router.get("/engagements/{engagement_id}/result", summary="Full audit result")
def get_result(engagement_id: str) -> dict[str, Any]:
    """Return the complete audit result: verdict, KPIs, artefacts, findings, matrix."""
    data = reader.load_full_result(engagement_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No audit result found for engagement '{engagement_id}'.",
        )
    return data


@router.get("/engagements/{engagement_id}/result/summary",
            summary="Verdict + KPIs only")
def get_result_summary(engagement_id: str) -> dict[str, Any]:
    """Return the final verdict and KPI scores only."""
    data = reader.load_audit_result(engagement_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Audit result not found.")
    return data


@router.get("/engagements/{engagement_id}/result/findings",
            summary="Findings and remediation roadmap")
def get_result_findings(engagement_id: str) -> dict[str, Any]:
    """Return blocking/positive findings and the remediation roadmap."""
    data = reader.load_findings(engagement_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Findings not found.")
    return data


@router.get("/engagements/{engagement_id}/result/compliance",
            summary="Compliance matrix")
def get_result_compliance(engagement_id: str) -> dict[str, Any]:
    """Return the article-to-verdict compliance matrix."""
    data = reader.load_compliance_matrix(engagement_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Compliance matrix not found.")
    return data
