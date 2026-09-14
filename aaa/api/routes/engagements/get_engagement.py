"""Part 2 of the former ``engagements`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from aaa.api.routes.engagements.router import (  # noqa: F401
    create_engagement,
    list_engagements,
    router,
)
from aaa.api.store import ENGAGEMENTS


@router.get("/{engagement_id}", summary="Get engagement")
def get_engagement(engagement_id: str) -> dict[str, Any]:
    """Retrieve an engagement by ID."""
    record = ENGAGEMENTS.get(engagement_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engagement '{engagement_id}' not found.",
        )
    return record
