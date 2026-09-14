"""Shared router and guards for the customer workflow endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aaa.api.store import ENGAGEMENTS

router = APIRouter(prefix="/api/v1/engagements", tags=["customer-workflow"])


def require_engagement(engagement_id: str) -> None:
    """Abort with 404 when the engagement does not exist.

    :param engagement_id: Engagement identifier from the path.
    :raises fastapi.HTTPException: 404 when the engagement is unknown.
    """
    if engagement_id not in ENGAGEMENTS:
        raise HTTPException(status_code=404,
                            detail=f"Engagement '{engagement_id}' not found.")
