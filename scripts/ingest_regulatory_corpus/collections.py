"""Qdrant client construction and collection management (Step 5)."""
from __future__ import annotations

import os
from typing import Any

from aaa.platform.embeddings.corpus_identity import stamp_identity
from scripts.ingest_regulatory_corpus.config import FILTER_KEYS, dense_dim
from scripts.ingest_regulatory_corpus.deps import require


def qdrant_client() -> Any:
    """Construct a Qdrant client from QDRANT_URL / QDRANT_API_KEY env vars."""
    qmod = require("qdrant_client")
    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    api_key = os.environ.get("QDRANT_API_KEY") or None
    return qmod.QdrantClient(url=url, api_key=api_key, prefer_grpc=False)


def _index_keys(client: Any, qmodels: Any, name: str, keys: tuple[str, ...]) -> None:
    """Create keyword payload indexes, ignoring already-existing ones."""
    for key in keys:
        try:
            client.create_payload_index(
                collection_name=name, field_name=key,
                field_schema=qmodels.PayloadSchemaType.KEYWORD)
        except Exception:  # pragma: no cover - index already exists
            pass


def ensure_corpus_collection(client: Any, name: str, reset: bool = False) -> None:
    """Create the hybrid (dense + sparse) collection and payload indexes."""
    qmodels = require("qdrant_client.models")
    exists = client.collection_exists(name)
    if exists and reset:
        client.delete_collection(name)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=name,
            vectors_config={"dense": qmodels.VectorParams(
                size=dense_dim(), distance=qmodels.Distance.COSINE)},
            sparse_vectors_config={"sparse": qmodels.SparseVectorParams(
                index=qmodels.SparseIndexParams(on_disk=False))},
        )
    _index_keys(client, qmodels, name, FILTER_KEYS)
    # Record which embedder built this corpus so a later provider swap is
    # refused at query time instead of silently returning bad hits.
    stamp_identity(client, name, "regulatory")


def ensure_obligations_collection(client: Any, name: str, reset: bool = False) -> None:
    """Create the dense-only obligations_index collection."""
    qmodels = require("qdrant_client.models")
    exists = client.collection_exists(name)
    if exists and reset:
        client.delete_collection(name)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(
                size=dense_dim(), distance=qmodels.Distance.COSINE),
        )
    _index_keys(client, qmodels, name, ("section_id", "question_id", "refs", "obligations",
                                        "entity_types", "risk_classes"))
    # Same guard as the corpus: the width check alone cannot tell two
    # 3072-dim models apart, so record which one built these vectors.
    stamp_identity(client, name, "regulatory")
