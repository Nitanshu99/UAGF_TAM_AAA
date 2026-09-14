"""Lazy client initialisation for the hybrid search path."""
from __future__ import annotations

import os

from aaa.agents.tier1.regulatory_rag.config import _SPARSE_MODEL


def ensure_qdrant(self) -> None:  # pragma: no cover
    """Lazy-initialise the Qdrant client alone.

    The identifier lookup (fix 16) reads a payload field and embeds nothing, so
    it must not drag in an embedding client or the BM25 encoder: on a host with
    no ``OPENAI_API_KEY`` that would raise, and the lookup would degrade to the
    built-in KB for a reason that has nothing to do with the corpus.
    """
    if self._qdrant is None:
        import qdrant_client

        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        self._qdrant = qdrant_client.QdrantClient(url=qdrant_url)


def ensure_clients(self) -> None:  # pragma: no cover
    """Lazy-initialise the Qdrant client and the fastembed BM25 encoder.

    The dense query vector comes from the ``regulatory`` embedding purpose
    (see :func:`~aaa.agents.tier1.regulatory_rag.vector.embed_query`), so no
    OpenAI client is built here: constructing one raised on any host without
    ``OPENAI_API_KEY`` — an OpenRouter or local embedding configuration — and
    the search silently fell back to the built-in KB for a key it never used.
    """
    ensure_qdrant(self)
    if self._sparse_encoder is None:
        # Optional live-retrieval extra (SETUP §9); absent in the default env.
        from fastembed import SparseTextEmbedding  # pyright: ignore[reportMissingImports]

        self._sparse_encoder = SparseTextEmbedding(model_name=_SPARSE_MODEL)
