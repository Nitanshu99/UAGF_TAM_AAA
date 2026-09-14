"""Part 1 of the former ``reader`` module (auto-split)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aaa.data.paths import (
    ARTEFACTS_FILE,
    AUDIT_RESULT_FILE,
    COMPLIANCE_MATRIX_FILE,
    ENGAGEMENT_FILE,
    FILES_META_FILE,
    FINDINGS_FILE,
    INTAKE_FILE,
    inputs_dir,
    results_dir,
)

logger = logging.getLogger(__name__)


def _read_json(path: Path) -> Any:
    """Return parsed JSON from *path*, or ``None`` if missing / corrupt."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return None


def load_engagement(engagement_id: str) -> dict[str, Any] | None:
    """Return the stored engagement creation record, or ``None``."""
    return _read_json(inputs_dir(engagement_id) / ENGAGEMENT_FILE)


def load_intake(engagement_id: str) -> dict[str, Any] | None:
    """Return the stored Stage A/B/C intake payload, or ``None``."""
    return _read_json(inputs_dir(engagement_id) / INTAKE_FILE)


def load_uploaded_files(engagement_id: str) -> list[dict[str, Any]]:
    """Return the list of uploaded-file metadata records (may be empty)."""
    data = _read_json(inputs_dir(engagement_id) / FILES_META_FILE)
    if isinstance(data, list):
        return data
    return []


def load_audit_result(engagement_id: str) -> dict[str, Any] | None:
    """Return the stored audit result (verdict + KPIs), or ``None``."""
    return _read_json(results_dir(engagement_id) / AUDIT_RESULT_FILE)


def load_artefacts(engagement_id: str) -> dict[str, Any] | None:
    """Return the phase artefact URI map, or ``None``."""
    return _read_json(results_dir(engagement_id) / ARTEFACTS_FILE)


def load_findings(engagement_id: str) -> dict[str, Any] | None:
    """Return blocking/positive findings and remediation roadmap, or ``None``."""
    return _read_json(results_dir(engagement_id) / FINDINGS_FILE)


def load_compliance_matrix(engagement_id: str) -> dict[str, Any] | None:
    """Return the article → verdict compliance matrix, or ``None``."""
    return _read_json(results_dir(engagement_id) / COMPLIANCE_MATRIX_FILE)
