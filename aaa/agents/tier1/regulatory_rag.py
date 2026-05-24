"""
RegulatoryRAG — Tier-1 cross-cutting agent (§3.1 #3).

Runtime:
  Production  – LlamaIndex ``VectorStoreIndex`` over the EU AI Act corpus stored
                in Qdrant (see §10, §14.4).  Initialised lazily on first search()
                call so the agent can be imported without Qdrant running.
  Offline     – When ``AAA_OFFLINE_MODE=true`` (or Qdrant unreachable) the agent
                falls back to a small hard-coded knowledge base covering the most
                commonly queried articles.  This keeps CI and the Streamlit demo
                self-contained.

search() return shape (one dict per chunk):
  {
    "text":    str,          # verbatim passage from the corpus
    "source":  str,          # citation label, e.g. "EU AI Act Art. 9 §1"
    "article": str,          # canonical article ID used in compliance_matrix
    "score":   float,        # cosine similarity [0, 1]; 1.0 for offline hits
  }
"""
from __future__ import annotations

import os
import logging
from typing import Any

from aaa.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Offline knowledge base — article → list of passage dicts
# ---------------------------------------------------------------------------
_OFFLINE_KB: dict[str, list[dict[str, Any]]] = {
    "Art.9": [
        {
            "text": (
                "Article 9 EU AI Act — Risk Management System. Providers of high-risk "
                "AI systems shall establish, implement, document and maintain a risk "
                "management system that runs throughout the entire lifecycle."
            ),
            "source": "EU AI Act Art. 9 §1",
            "article": "Art.9",
            "score": 1.0,
        }
    ],
    "Art.10": [
        {
            "text": (
                "Article 10 EU AI Act — Data and Data Governance. Training, validation "
                "and testing data sets shall be subject to appropriate data governance "
                "and management practices. Data sets shall be relevant, sufficiently "
                "representative and, to the best extent possible, free of errors."
            ),
            "source": "EU AI Act Art. 10 §2",
            "article": "Art.10",
            "score": 1.0,
        }
    ],
    "Art.13": [
        {
            "text": (
                "Article 13 EU AI Act — Transparency and Provision of Information. "
                "High-risk AI systems shall be designed and developed in such a way "
                "to ensure that their operation is sufficiently transparent to enable "
                "deployers to interpret the system's output and use it appropriately."
            ),
            "source": "EU AI Act Art. 13 §1",
            "article": "Art.13",
            "score": 1.0,
        }
    ],
    "Art.43": [
        {
            "text": (
                "Article 43 EU AI Act — Conformity Assessment. For high-risk AI systems "
                "listed in Annex III, point 1, the provider shall follow the conformity "
                "assessment procedure set out in Annex VII (third-party) or conduct "
                "internal control pursuant to Annex VI."
            ),
            "source": "EU AI Act Art. 43 §1",
            "article": "Art.43",
            "score": 1.0,
        }
    ],
    "Annex_III": [
        {
            "text": (
                "Annex III EU AI Act — High-Risk AI Systems. Includes biometric "
                "identification (§1), critical infrastructure (§2), education (§3), "
                "employment (§4), essential services (§5), law enforcement (§6), "
                "migration and border control (§7), administration of justice (§8)."
            ),
            "source": "EU AI Act Annex III",
            "article": "Annex_III",
            "score": 1.0,
        }
    ],
    "GPAI_51": [
        {
            "text": (
                "Article 51 EU AI Act — Classification of GPAI Models with Systemic Risk. "
                "A GPAI model shall be classified as a model with systemic risk if it has "
                "high impact capabilities evaluated on the basis of appropriate technical "
                "tools and methodologies, including indicators and benchmarks."
            ),
            "source": "EU AI Act Art. 51 §1",
            "article": "GPAI_51",
            "score": 1.0,
        }
    ],
}

# Simple keyword → article mapping for fuzzy offline lookup
_KEYWORD_MAP: dict[str, str] = {
    "risk management": "Art.9",
    "article 9": "Art.9",
    "data governance": "Art.10",
    "article 10": "Art.10",
    "transparency": "Art.13",
    "article 13": "Art.13",
    "conformity": "Art.43",
    "article 43": "Art.43",
    "annex iii": "Annex_III",
    "high-risk": "Annex_III",
    "gpai": "GPAI_51",
    "general purpose": "GPAI_51",
}


class RegulatoryRAG(BaseAgent):
    """
    Cross-cutting regulatory search agent.

    Provides ``search(query, top_k)`` to all phase agents and the Orchestrator.
    Uses LlamaIndex + Qdrant in production; offline KB when
    ``AAA_OFFLINE_MODE=true`` or the index is unavailable.
    """

    def __init__(self, model: str = "claude-3-haiku-20240307"):
        super().__init__(name="Regulatory RAG", model=model)
        self.corpus_path = "data/regulatory_corpus"
        self._index: Any = None  # lazy-loaded LlamaIndex VectorStoreIndex
        self._offline: bool = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, query: str) -> str:  # type: ignore[override]
        """Return the top search result as a plain string (used by agent prompts)."""
        hits = self.search(query, top_k=1)
        if hits:
            return hits[0]["text"]
        return f"No regulatory passage found for: {query}"

    # ------------------------------------------------------------------
    # Public search API
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search the EU AI Act corpus for passages relevant to *query*.

        Parameters
        ----------
        query:
            Free-text question or keyword string.
        top_k:
            Maximum number of results to return.

        Returns
        -------
        list[dict]  – each dict has keys: text, source, article, score.
        """
        if not self._offline:
            try:
                return self._vector_search(query, top_k)
            except Exception as exc:  # pragma: no cover
                logger.warning("Qdrant search failed (%s); falling back to offline KB.", exc)

        return self._offline_search(query, top_k)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_index(self) -> None:  # pragma: no cover
        """Lazy-initialise the LlamaIndex VectorStoreIndex backed by Qdrant."""
        if self._index is not None:
            return
        try:
            from llama_index.core import VectorStoreIndex, StorageContext
            from llama_index.vector_stores.qdrant import QdrantVectorStore
            import qdrant_client

            qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
            collection = os.environ.get("QDRANT_COLLECTION", "eu_ai_act")
            client = qdrant_client.QdrantClient(url=qdrant_url)
            vector_store = QdrantVectorStore(client=client, collection_name=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            self._index = VectorStoreIndex.from_vector_store(
                vector_store, storage_context=storage_context
            )
        except Exception as exc:
            logger.warning("Could not initialise Qdrant index: %s", exc)
            raise

    def _vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:  # pragma: no cover
        """Run a live vector search against the Qdrant-backed LlamaIndex."""
        self._ensure_index()
        retriever = self._index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        results = []
        for node in nodes:
            meta = node.metadata or {}
            results.append({
                "text": node.get_content(),
                "source": meta.get("source", "EU AI Act"),
                "article": meta.get("article", ""),
                "score": float(node.score or 0.0),
            })
        return results

    def _offline_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Return results from the hard-coded offline knowledge base."""
        q_lower = query.lower()
        # Direct article match
        for keyword, article_id in _KEYWORD_MAP.items():
            if keyword in q_lower:
                hits = _OFFLINE_KB.get(article_id, [])
                if hits:
                    return hits[:top_k]
        # Fallback: return all KB entries scored by simple overlap
        candidates: list[tuple[float, dict[str, Any]]] = []
        for article_id, passages in _OFFLINE_KB.items():
            for passage in passages:
                words = set(q_lower.split())
                text_words = set(passage["text"].lower().split())
                overlap = len(words & text_words) / max(len(words), 1)
                candidates.append((overlap, passage))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in candidates[:top_k]]

