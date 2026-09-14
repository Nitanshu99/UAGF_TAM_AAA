"""Vector search over an engagement's client-document collection."""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.embeddings.guard import ProviderMismatchError, assert_provider_matches
from aaa.tools.client_doc_ingest.config import _VECTOR_NAME, _collection_name, _embeddings_available
from aaa.tools.client_doc_ingest.embed import _embed
from aaa.tools.client_doc_ingest.qdrant import _collection_exists, _qdrant_client

logger = logging.getLogger(__name__)


def _hit(point: Any) -> dict[str, Any]:
    """Normalise one Qdrant point into the search-hit contract."""
    payload = getattr(point, "payload", None) or {}
    return {
        "text": payload.get("text", ""),
        "source_uri": payload.get("source_uri", ""),
        "source_sha256": payload.get("source_sha256", ""),
        "document_role": payload.get("document_role", "unknown"),
        "page_number": payload.get("page_number"),
        "section_hint": payload.get("section_hint"),
        "chunk_index": payload.get("chunk_index", 0),
        "chunk_total": payload.get("chunk_total", 0),
        "score": float(getattr(point, "score", 0.0) or 0.0),
    }


def client_doc_search(engagement_id: str, query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Search the engagement's collection; returns ``[]`` when unavailable.

    :param engagement_id: Engagement whose collection is queried.
    :param query: Free-text query embedded and matched against chunks.
    :param top_k: Maximum number of hits.
    """
    if not _embeddings_available():
        return []
    collection = _collection_name(engagement_id)
    try:
        client = _qdrant_client()
        if not _collection_exists(client, collection):
            return []
        try:
            assert_provider_matches(
                client, collection, "client_docs", "EMBEDDINGS_CLIENT_DOCS")
        except ProviderMismatchError as exc:
            # Logged at error, not swallowed into the generic warning below:
            # returning [] here is indistinguishable from "the dossier had no
            # match", which would misread a configuration fault as an absence
            # of client evidence. No hits is the safe direction — the agent
            # abstains rather than citing wrongly-ranked documents — but the
            # operator has to be told why.
            logger.error("client_doc_search refused for %s: %s", engagement_id, exc)
            return []
        vector = _embed([query])[0]
        response = client.query_points(
            collection_name=collection,
            query=vector,
            using=_VECTOR_NAME,
            limit=top_k,
            with_payload=True,
        )
        return [_hit(point) for point in response.points]
    except Exception as exc:  # pragma: no cover - no-service fallback
        logger.warning("client_doc_search unavailable for %s: %s", engagement_id, exc)
        return []
