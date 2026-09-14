"""Part 1 of the former ``data`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aaa.data import reader

router = APIRouter(prefix="/api/v1/data", tags=["data-store"])


@router.get("/engagements", summary="List all stored engagements")
def list_stored_engagements() -> list[dict[str, Any]]:
    """Return the master index: one summary row per stored engagement."""
    return reader.list_engagements()


@router.get("/results", summary="List completed engagements")
def list_stored_results() -> list[dict[str, Any]]:
    """Return index rows for engagements that have a final verdict."""
    return reader.list_results()


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
