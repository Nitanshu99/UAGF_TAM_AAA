"""File-upload endpoint for customer artefacts."""
from __future__ import annotations

from typing import Any

from fastapi import File, Form, UploadFile

from aaa.api.routes.workflow.base import require_engagement, router
from aaa.api.store import get_store
from aaa.data.models import UploadedFileMeta
from aaa.data.writer import save_uploaded_file


@router.post("/{engagement_id}/files", summary="Upload customer file")
async def upload_file(
    engagement_id: str,
    role: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Store a customer-uploaded artefact and return its EvidenceStore URI.

    :param engagement_id: Engagement the file belongs to.
    :param role: Artefact role, e.g. ``model_card`` or ``training_data``.
    :param file: The uploaded file.
    :returns: ``{uri, sha256, role}`` for the stored artefact.
    """
    require_engagement(engagement_id)
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
