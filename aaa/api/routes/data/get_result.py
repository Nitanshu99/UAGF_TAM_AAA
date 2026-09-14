"""Part 2 of the former ``data`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from aaa.api.routes.data.router import (  # noqa: F401
    get_input,
    get_input_engagement,
    get_input_files,
    get_input_intake,
    list_stored_engagements,
    list_stored_results,
    router,
)
from aaa.data import reader


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
