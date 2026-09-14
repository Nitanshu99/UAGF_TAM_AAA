"""Audit-state and HITL-review read endpoints."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from aaa.api.routes.workflow.base import router
from aaa.api.store import FINAL_STATES


def _load_customer_json(engagement_id: str, suffix: str) -> dict[str, Any] | None:
    """Read a persisted customer artefact (audit_state / hitl_review) from disk.

    Files live at ``data/customer/<company>/<id>_<suffix>.json``; globbing by
    id means the caller need not know the company folder.

    :param engagement_id: Engagement identifier.
    :param suffix: Artefact suffix, ``audit_state`` or ``hitl_review``.
    :returns: Parsed JSON, or ``None`` when absent/unreadable.
    """
    for path in Path("data/customer").glob(f"*/{engagement_id}_{suffix}.json"):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # pylint: disable=broad-exception-caught
            continue
    return None


@router.get("/{engagement_id}/audit-state", summary="Full final audit-state JSON")
def get_audit_state(engagement_id: str) -> dict[str, Any]:
    """Return the complete final audit-state object.

    Includes verdict, KPIs, compliance matrix, article evidence, verifier
    critiques, findings and the CGSA payload.  Served from the in-memory
    result when available, else from the persisted customer artefact.

    :param engagement_id: Engagement identifier.
    :returns: The final audit state.
    :raises fastapi.HTTPException: 404 when no state exists.
    """
    state = FINAL_STATES.get(engagement_id) or _load_customer_json(engagement_id, "audit_state")
    if state is None:
        raise HTTPException(status_code=404,
                            detail=f"No audit state found for engagement '{engagement_id}'.")
    return state


@router.get("/{engagement_id}/hitl-review", summary="HITL review packet")
def get_hitl_review(engagement_id: str) -> dict[str, Any]:
    """Return the deferred-HITL review packet.

    :param engagement_id: Engagement identifier.
    :returns: Escalated cases + evidence + editable human fields.
    :raises fastapi.HTTPException: 404 when no packet exists.
    """
    packet = _load_customer_json(engagement_id, "hitl_review")
    if packet is None:
        raise HTTPException(
            status_code=404,
            detail=f"No HITL review packet for engagement '{engagement_id}' "
                   "(none required, or run not completed).")
    return packet
