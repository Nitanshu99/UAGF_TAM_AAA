"""The content-addressed URI, index entry and payload of one stored file."""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from typing import Any


def file_record(engagement_id: str, phase: str, artefact_type: str, filename: str,
                content_type: str, data: bytes,
                agent_name: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """``(uri, index_entry, payload)`` for *data*; the URI carries the content hash.

    :param engagement_id: Engagement the file belongs to.
    :param phase: Pipeline phase key, e.g. ``"customer_uploads"``.
    :param artefact_type: Role of the file, e.g. ``"technical_doc"``.
    :param filename: Original filename (sanitised into the URI).
    :param content_type: MIME type of the upload.
    :param data: Raw file bytes (persisted base64-encoded).
    :param agent_name: Producing agent (provenance).
    """
    sha256 = hashlib.sha256(data).hexdigest()
    safe_name = filename.replace("/", "_").replace("\\", "_") or "upload.bin"
    uri = f"minio://{engagement_id}/{phase}/{artefact_type}_{sha256[:8]}_{safe_name}"
    entry = {"engagement_id": engagement_id, "phase": phase, "artefact_type": artefact_type,
             "filename": filename, "content_type": content_type, "bytes_size": len(data),
             "uri": uri, "sha256": sha256,
             "created_at": datetime.now(timezone.utc).isoformat(),
             "created_by_agent": agent_name}
    payload = {"filename": filename, "content_type": content_type, "bytes_size": len(data),
               "sha256": sha256, "body_base64": base64.b64encode(data).decode("ascii")}
    return uri, entry, payload


__all__ = ["file_record"]
