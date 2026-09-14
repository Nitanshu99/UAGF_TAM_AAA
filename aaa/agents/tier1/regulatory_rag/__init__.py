"""RegulatoryRAG — Tier-1 cross-cutting agent (§3.1 #3).

Runtime:
  Production  – Direct hybrid query against the Qdrant ``regulatory_corpus``
                collection populated by ``scripts/ingest_regulatory_corpus.py``.
                Dense vectors come from OpenAI ``text-embedding-3-large``;
                sparse vectors from fastembed BM25 (``Qdrant/bm25``); the two
                are fused server-side via Reciprocal Rank Fusion.  Initialised
                lazily on first ``search()`` so the agent can be imported
                without Qdrant or ``OPENAI_API_KEY``.
  Fallback    – When Qdrant is unreachable the agent falls back to a small
                built-in knowledge base covering the most commonly queried
                articles.  This keeps CI and the Streamlit demo self-contained.
"""
from __future__ import annotations

from aaa.agents.tier1.regulatory_rag.agent import RegulatoryRAG
from aaa.agents.tier1.regulatory_rag.factory import build_regulatory_rag
from aaa.agents.tier1.regulatory_rag.hits import _locator, _point_to_hit  # noqa: F401 (tests)

__all__ = ["RegulatoryRAG", "build_regulatory_rag"]
