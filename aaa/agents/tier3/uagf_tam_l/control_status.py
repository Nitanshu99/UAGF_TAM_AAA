"""Reading a declared control's status out of the guardrail and RAG configuration."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


#: Where a config states which of its own controls are live. Clients name this
#: block inconsistently, so the common spellings are all accepted.
_STATUS_KEYS = ("implementation_status", "status", "deployment_status")
#: Buckets within that block, mapped to the one word the audit uses.
_BUCKETS = {
    "implemented": "implemented",
    "fully_implemented": "implemented",
    "partially_implemented": "partial",
    "partial": "partial",
    "not_yet_implemented": "not_implemented",
    "not_implemented": "not_implemented",
    "planned": "not_implemented",
}
def _load(uri: str | None, store: Any, label: str) -> dict[str, Any] | None:
    """Load one declared-control document, or ``None`` if it cannot be read."""
    if not uri:
        return None
    try:
        from aaa.platform.artifact_loader import load_artifact_from_uri
        content = load_artifact_from_uri(uri, store, "json")
    except Exception as exc:  # noqa: BLE001 — evidence is best-effort, never fatal
        logger.warning("%s %s could not be loaded: %s", label, uri, exc)
        return None
    if not isinstance(content, dict):
        logger.warning("%s %s is not a JSON object; ignoring.", label, uri)
        return None
    return content
def control_status(config: dict[str, Any]) -> dict[str, list[str]]:
    """Which of a config's own controls it declares live, partial or absent.

    :param config: A parsed guardrail configuration.
    :returns: ``implemented`` / ``partial`` / ``not_implemented`` control names.
    """
    block: dict[str, Any] = {}
    for key in _STATUS_KEYS:
        candidate = config.get(key)
        if isinstance(candidate, dict):
            block = candidate
            break
    out: dict[str, list[str]] = {"implemented": [], "partial": [], "not_implemented": []}
    for raw, bucket in _BUCKETS.items():
        value = block.get(raw)
        if isinstance(value, list):
            out[bucket].extend(str(v) for v in value)
    return out


__all__ = ["_BUCKETS", "_STATUS_KEYS", "_load", "control_status"]
