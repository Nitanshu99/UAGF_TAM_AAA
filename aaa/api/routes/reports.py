"""
aaa.api.routes.reports — Audit report retrieval endpoints.

Endpoints
---------
GET /api/v1/engagements/{id}/report      — JSON KPI summary + artefact URIs
GET /api/v1/engagements/{id}/report.pdf  — rendered PDF bytes
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from aaa.api.store import FINAL_STATES, get_store

router = APIRouter(prefix="/api/v1/engagements", tags=["reports"])


@router.get("/{engagement_id}/report", summary="Get audit report summary")
def get_report(engagement_id: str) -> dict[str, Any]:
    """Return final verdict, KPI summary, and report artefact URIs."""
    final = FINAL_STATES.get(engagement_id)
    if final is None:
        raise HTTPException(status_code=404, detail="Report not available.")
    store = get_store(engagement_id)
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


@router.get("/{engagement_id}/report.pdf", summary="Download rendered PDF")
def get_report_pdf(engagement_id: str) -> Response:
    """Return rendered PDF bytes when ReportLab output is available."""
    report = get_report(engagement_id)
    store = get_store(engagement_id)
    payload = store.get_artefact(report.get("pdf_uri") or "") or {}
    if payload.get("encoding") != "latin-1":
        raise HTTPException(status_code=404, detail="Rendered PDF not available.")
    return Response(
        content=str(payload.get("body", "")).encode("latin-1"),
        media_type="application/pdf",
    )
