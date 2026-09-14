"""Persist user inputs: engagement creation, intake payloads, file uploads."""
from __future__ import annotations

import logging
from typing import Any

from aaa.data import index as idx
from aaa.data.models import EngagementRecord, IntakeRecord, UploadedFileMeta
from aaa.data.paths import ENGAGEMENT_FILE, FILES_META_FILE, INTAKE_FILE, inputs_dir
from aaa.data.writer.atomic import _append_list, _write

logger = logging.getLogger(__name__)


def save_engagement(record: EngagementRecord) -> None:
    """Persist engagement creation data entered by the user.

    Writes ``data/inputs/<id>/engagement.json`` and updates the index.

    :param record: The engagement creation record.
    """
    path = inputs_dir(record.engagement_id) / ENGAGEMENT_FILE
    _write(path, record.to_dict())
    idx.upsert({
        "engagement_id": record.engagement_id,
        "provider_name": record.provider_name,
        "system_name": record.system_name,
        "declared_risk_tier": record.declared_risk_tier,
        "status": record.status,
        "final_verdict": None,
        "created_at": record.created_at,
        "completed_at": None,
    })
    logger.debug("Saved engagement input: %s", record.engagement_id)


def save_intake(engagement_id: str, stage_a: dict[str, Any],
                stage_b: dict[str, Any], stage_c: dict[str, Any] | None) -> None:
    """Persist the Stage A/B/C payloads to ``data/inputs/<id>/intake.json``.

    :param engagement_id: Engagement identifier.
    :param stage_a: Stage A triage payload.
    :param stage_b: Stage B Annex IV payload.
    :param stage_c: Optional Stage C access payload.
    """
    record = IntakeRecord(engagement_id=engagement_id, stage_a=stage_a,
                          stage_b=stage_b, stage_c=stage_c)
    _write(inputs_dir(engagement_id) / INTAKE_FILE, record.to_dict())
    idx.upsert({"engagement_id": engagement_id, "status": "intake_submitted"})
    logger.debug("Saved intake payload: %s", engagement_id)


def save_uploaded_file(meta: UploadedFileMeta) -> None:
    """Append a file-upload metadata entry to ``data/inputs/<id>/files.json``.

    :param meta: Upload metadata record.
    """
    _append_list(inputs_dir(meta.engagement_id) / FILES_META_FILE, meta.to_dict())
    logger.debug("Saved file meta: %s → %s", meta.engagement_id, meta.filename)
