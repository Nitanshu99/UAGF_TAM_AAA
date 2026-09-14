"""Hybrid dense + sparse Qdrant search (production path).

Functions take the agent instance first so lazily-created clients are
cached on it; they are bound as methods on :class:`RegulatoryRAG`.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.regulatory_rag.clients import ensure_clients
from aaa.agents.tier1.regulatory_rag.config import (
    _DENSE_VECTOR_NAME,
    _PREFETCH_LIMIT,
    _SPARSE_VECTOR_NAME,
)
from aaa.agents.tier1.regulatory_rag.hits import _point_to_hit
from aaa.agents.tier1.regulatory_rag.provider_guard import assert_corpus_provider


def embed_query(self, query: str) -> tuple[list[float], dict[str, list]]:  # pragma: no cover
    """Return ``(dense_vector, sparse_vector)`` for *query*.

    The dense half goes through the ``regulatory`` embedding purpose so the
    provider can be swapped; it must match whatever embedded the corpus, which
    :func:`assert_corpus_provider` checks before the search runs.
    """
    from aaa.platform.embeddings import embed_texts

    dense_vec = embed_texts([query], "regulatory")[0]
    sparse = next(iter(self._sparse_encoder.embed([query])))
    sparse_vec = {
        "indices": [int(i) for i in sparse.indices],
        "values": [float(v) for v in sparse.values],
    }
    return dense_vec, sparse_vec

def vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:  # pragma: no cover
    """Hybrid dense + sparse search against Qdrant with RRF fusion."""
    ensure_clients(self)
    assert_corpus_provider(self._qdrant, self._collection)
    from qdrant_client import models as qmodels

    dense_vec, sparse_vec = embed_query(self, query)
    response = self._qdrant.query_points(
        collection_name=self._collection,
        prefetch=[
            qmodels.Prefetch(
                query=dense_vec,
                using=_DENSE_VECTOR_NAME,
                limit=_PREFETCH_LIMIT,
            ),
            qmodels.Prefetch(
                query=qmodels.SparseVector(
                    indices=sparse_vec["indices"],
                    values=sparse_vec["values"],
                ),
                using=_SPARSE_VECTOR_NAME,
                limit=_PREFETCH_LIMIT,
            ),
        ],
        query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
        limit=top_k,
        with_payload=True,
    )
    return [_point_to_hit(p) for p in response.points]
