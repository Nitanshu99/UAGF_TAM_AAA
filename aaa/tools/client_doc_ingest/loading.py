"""Document-role tagging and byte-loading helpers."""
from __future__ import annotations

import base64
import json
from typing import Any

from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest.config import _filename

_ROLE_MARKERS = {
    "risk_management_file": ("risk_management", "risk-management"),
    "post_market_plan": ("post_market", "post-market"),
    "eu_declaration": ("eu_doc", "eu_declaration", "declaration"),
    "system_prompt": ("system_prompt", "system-prompt"),
    "rag_manifest": ("rag_manifest", "rag-manifest"),
    "guardrail_config": ("guardrail",),
    "golden_set": ("golden_set", "golden-set"),
}


def _document_role(uri: str) -> str:
    """Classify a document's compliance role from its filename."""
    name = _filename(uri).lower()
    for role, markers in _ROLE_MARKERS.items():
        if any(marker in name for marker in markers):
            return role
    return "unknown"


def _coerce_bytes(content: Any) -> bytes:
    """Coerce an evidence-store payload into raw bytes."""
    if isinstance(content, dict) and isinstance(content.get("body_base64"), str):
        return base64.b64decode(content["body_base64"])
    if isinstance(content, bytes):
        return content
    if isinstance(content, bytearray):
        return bytes(content)
    if isinstance(content, str):
        return content.encode("utf-8")
    return json.dumps(content, indent=2, default=str).encode("utf-8")


def _load_document(uri: str, store: EvidenceStore | None) -> bytes | None:
    """Resolve a ``minio://`` URI to document bytes, or ``None``."""
    if uri.startswith("minio://") and store is not None:
        content = store.get_artefact(uri)
        return None if content is None else _coerce_bytes(content)
    return None
