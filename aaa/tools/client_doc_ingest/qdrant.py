"""Qdrant client construction and collection management."""
from __future__ import annotations

import os
from typing import Any

from aaa.platform.embeddings.corpus_identity import stamp_identity
from aaa.tools.client_doc_ingest.config import _VECTOR_NAME, _dense_dim


def _qdrant_client() -> Any:
    """Build a Qdrant client from ``QDRANT_URL`` / ``QDRANT_API_KEY``."""
    import qdrant_client

    return qdrant_client.QdrantClient(
        url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        api_key=os.environ.get("QDRANT_API_KEY") or None,
        prefer_grpc=False,
        check_compatibility=False,
    )


def _ensure_collection(client: Any, collection: str) -> None:
    """Create the dense collection + payload indexes when absent."""
    from qdrant_client import models as qmodels

    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config={
                _VECTOR_NAME: qmodels.VectorParams(
                    size=_dense_dim(), distance=qmodels.Distance.COSINE,
                )
            },
        )
    for key in ("source_uri", "document_role", "source_sha256"):
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=key,
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception:  # pragma: no cover - index already exists
            pass
    # Record which embedder indexed this engagement's documents, so changing
    # EMBEDDINGS_CLIENT_DOCS later is refused at search time rather than
    # silently matching new query vectors against old ones.
    stamp_identity(client, collection, "client_docs")


def _collection_exists(client: Any, collection: str) -> bool:
    """True when *collection* exists (never raises)."""
    try:
        return bool(client.collection_exists(collection))
    except Exception:
        return False
