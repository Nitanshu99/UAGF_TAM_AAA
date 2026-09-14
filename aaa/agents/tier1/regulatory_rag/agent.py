"""The RegulatoryRAG class — cross-cutting regulatory search agent."""
from __future__ import annotations

import os
from typing import Any

from aaa.agents.base import BaseAgent
from aaa.agents.tier1.regulatory_rag.builtin import builtin_search
from aaa.agents.tier1.regulatory_rag.lookup import kb_lookup, qdrant_lookup
from aaa.agents.tier1.regulatory_rag.query import lookup as _lookup
from aaa.agents.tier1.regulatory_rag.query import search as _search
from aaa.agents.tier1.regulatory_rag.render import render_hit
from aaa.agents.tier1.regulatory_rag.vector import vector_search
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class RegulatoryRAG(BaseAgent):
    """Cross-cutting regulatory search agent.

    Provides ``search(query, top_k)`` to all phase agents and the
    Orchestrator.  Uses a direct Qdrant hybrid query (dense + sparse, fused
    via RRF) in production; falls back to a built-in KB when the Qdrant
    collection is unavailable.
    """

    #: bound implementations (kept as methods for test monkeypatching)
    _vector_search = vector_search
    _builtin_search = staticmethod(builtin_search)
    _qdrant_lookup = qdrant_lookup
    _kb_lookup = staticmethod(kb_lookup)

    def __init__(self, model: str | None = None, service_tier: str | None = None):
        super().__init__(
            name="Regulatory RAG",
            model=resolve_model("Regulatory RAG", model),
            service_tier=resolve_service_tier("Regulatory RAG", service_tier),
        )
        self.corpus_path = "data/regulatory_corpus"
        self._qdrant: Any = None          # lazy-loaded qdrant_client.QdrantClient
        self._sparse_encoder: Any = None  # lazy-loaded fastembed.SparseTextEmbedding
        self._collection: str = os.environ.get("QDRANT_COLLECTION", "regulatory_corpus")

    @property
    def collection(self) -> str:
        """Name of the Qdrant collection this agent searches."""
        return self._collection

    async def process(self, message: str) -> str:  # type: ignore[override]
        """Return the retrieved passages for *message* as citable text.

        This agent retrieves; it does not generate. ``process`` exists because
        :class:`BaseAgent` declares it abstract, and it is a formatted view of
        :meth:`search` — the same passages, rendered for a caller that wants a
        string. It makes **no LLM call**.

        It used to. A synthesis step asked a model to condense the passages
        into a prose answer, which put a second model between the corpus and
        the auditor: a paraphrase cannot be cited in a conformity opinion, and
        every summary is a place a citation can drift. The phase agents are the
        readers of the law — they inject these passages into their own prompts
        and quote them (``regulatory_hits``, fix 1; de-duplicated and ranked,
        fix 9). One model between the law and the report, not two.

        :param message: Free-text regulatory question.
        :type message: str
        :returns: One line per passage, ``"<source> [<locator>]: <text>"``, or a
            note naming the query when the corpus returns nothing.
        :rtype: str
        """
        hits = self.search(message, top_k=3)
        if not hits:
            return f"No regulatory passage found for: {message}"
        return "\n\n".join(render_hit(hit) for hit in hits)

    #: Retrieval, implemented in :mod:`aaa.agents.tier1.regulatory_rag.query` and
    #: bound here so both stay methods a test can monkeypatch on the instance.
    search = _search
    lookup = _lookup
