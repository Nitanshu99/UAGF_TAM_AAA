"""Public entry point: ingest client documents into Qdrant."""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest.config import (
    ClientDocIngestError,
    _collection_name,
    _embeddings_available,
)
from aaa.tools.client_doc_ingest.freshness import reset_for_run
from aaa.tools.client_doc_ingest.pipeline import _collect_chunks, _upsert_chunks
from aaa.tools.client_doc_ingest.qdrant import _ensure_collection, _qdrant_client

logger = logging.getLogger(__name__)


def client_doc_ingest(
    engagement_id: str,
    doc_uris: list[str],
    store: EvidenceStore | None = None,
) -> dict[str, Any]:
    """Ingest client-uploaded documents into a per-engagement collection.

    :param engagement_id: Engagement the documents belong to.
    :param doc_uris: Evidence-store URIs of the uploaded documents.
    :param store: Evidence store used to resolve the URIs.
    :returns: ``{collection_name, chunks_indexed, sources}``.
    :raises ClientDocIngestError: On unexpected Qdrant/OpenAI failures.
    """
    collection = _collection_name(engagement_id)
    if not doc_uris:
        return {"collection_name": collection, "chunks_indexed": 0, "sources": []}
    if not _embeddings_available():
        from aaa.platform.embeddings import missing_credential
        logger.info(
            "Skipping client_doc_ingest for %s because %s is not configured.",
            engagement_id, missing_credential("client_docs"),
        )
        return {"collection_name": collection, "chunks_indexed": 0, "sources": []}

    try:
        client = _qdrant_client()
        reset_for_run(client, collection, engagement_id)
        _ensure_collection(client, collection)
        chunks, sources = _collect_chunks(client, collection, doc_uris, store)
        if not chunks:
            return {"collection_name": collection, "chunks_indexed": 0, "sources": sources}
        written = _upsert_chunks(client, collection, chunks)
        return {"collection_name": collection, "chunks_indexed": written, "sources": sources}
    except Exception as exc:  # noqa: BLE001
        raise ClientDocIngestError(str(exc)) from exc
