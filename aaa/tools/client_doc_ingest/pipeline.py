"""Chunk collection, embedding, and batch upsert for ingestion."""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest.chunking import _chunks_for_document, _point_id
from aaa.tools.client_doc_ingest.config import _UPSERT_BATCH, _VECTOR_NAME
from aaa.tools.client_doc_ingest.embed import _embed
from aaa.tools.client_doc_ingest.loading import _load_document
from aaa.tools.client_doc_ingest.source_check import _source_exists

logger = logging.getLogger(__name__)


def _collect_chunks(client: Any, collection: str, doc_uris: list[str],
                    store: EvidenceStore | None) -> tuple[list[dict[str, Any]], list[str]]:
    """Load and chunk every not-yet-indexed document.

    :returns: ``(chunks, source_uris)`` — already-indexed sources are kept in
        the source list without re-chunking.
    """
    chunks: list[dict[str, Any]] = []
    sources: list[str] = []
    for uri in doc_uris:
        if _source_exists(client, collection, uri):
            sources.append(uri)
            continue
        data = _load_document(uri, store)
        if data is None:
            logger.warning("Client document not found for ingestion: %s", uri)
            continue
        doc_chunks = _chunks_for_document(uri, data)
        chunks.extend(doc_chunks)
        if doc_chunks:
            sources.append(uri)
    return chunks, sources


def _upsert_chunks(client: Any, collection: str, chunks: list[dict[str, Any]]) -> int:
    """Embed and batch-upsert *chunks*; returns the number written."""
    from qdrant_client import models as qmodels

    vectors = _embed([chunk["text"] for chunk in chunks])
    written = 0
    for start in range(0, len(chunks), _UPSERT_BATCH):
        batch = chunks[start:start + _UPSERT_BATCH]
        batch_vectors = vectors[start:start + _UPSERT_BATCH]
        points = [
            qmodels.PointStruct(id=_point_id(chunk), payload=chunk,
                                vector={_VECTOR_NAME: vector})
            for chunk, vector in zip(batch, batch_vectors, strict=True)
        ]
        client.upsert(collection_name=collection, points=points, wait=True)
        written += len(points)
    return written
