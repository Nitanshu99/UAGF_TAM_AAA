"""Client-document ingestion into the per-engagement collection (Stage 0B)."""
from __future__ import annotations

from typing import Any

from aaa.agents.intake_validator.errors import _CLIENT_DOC_URI_FIELDS
from aaa.tools.client_doc_ingest import ClientDocIngestError, client_doc_ingest


def ingest_client_docs(agent: Any, engagement_id: str, stage_b_payload: dict[str, Any],
                       t01c_content: dict[str, Any]) -> str | None:
    """Index the uploaded supporting documents; failures are non-fatal.

    A translated ingest failure is surfaced as a warning on the T01c
    artefact rather than blocking intake processing.

    :param agent: The IntakeValidator (evidence store).
    :param engagement_id: Engagement identifier.
    :param stage_b_payload: Validated Stage B payload (carries the URIs).
    :param t01c_content: T01c payload (warnings appended in place).
    :returns: The Qdrant collection name, or ``None``.
    """
    doc_uris = [
        uri for uri in (stage_b_payload.get(field) for field in _CLIENT_DOC_URI_FIELDS)
        if isinstance(uri, str) and uri
    ]
    if not doc_uris:
        return None
    try:
        ingest_result = client_doc_ingest(
            engagement_id=engagement_id, doc_uris=doc_uris, store=agent.store)
        return ingest_result.get("collection_name")
    except ClientDocIngestError as exc:
        t01c_content.setdefault("warnings", []).append(f"client_doc_ingest failed: {exc}")
        return None
