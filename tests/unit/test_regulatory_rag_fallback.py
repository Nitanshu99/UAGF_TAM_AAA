"""RegulatoryRAG built-in KB fallback path (no network, no credentials)."""
from __future__ import annotations

import asyncio

import pytest

from aaa.agents.tier1.regulatory_rag import RegulatoryRAG


@pytest.fixture
def fallback_rag(monkeypatch):
    """RegulatoryRAG whose vector search is unavailable (forces built-in KB)."""
    rag = RegulatoryRAG()

    def _raise(query, top_k):
        raise ConnectionError("qdrant unavailable in unit tests")

    monkeypatch.setattr(rag, "_vector_search", _raise)
    return rag


class TestRegulatoryRAGFallback:
    """Verify the built-in KB path works without any external dependencies."""

    def test_search_returns_list(self, fallback_rag):
        assert isinstance(fallback_rag.search("risk management system", top_k=3), list)

    def test_search_result_keys(self, fallback_rag):
        hits = fallback_rag.search("Article 9 risk management", top_k=1)
        assert hits, "Expected at least one built-in KB hit"
        assert set(hits[0].keys()) >= {"text", "source", "article", "score"}

    def test_search_respects_top_k(self, fallback_rag):
        hits = fallback_rag.search("ai system transparency obligation", top_k=2)
        assert len(hits) <= 2

    def test_process_returns_string(self, fallback_rag):
        result = asyncio.run(fallback_rag.process("risk management"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_no_match_returns_fallback(self, fallback_rag):
        # May be empty or the lowest-score candidate.
        assert isinstance(fallback_rag.search("zzzzznomatch12345", top_k=1), list)
