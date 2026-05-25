"""
Unit tests for aaa.agents.tier1.regulatory_rag.

Covers:
  - _point_to_hit: all payload combinations → correct {text, source, article, score}
  - RegulatoryRAG._offline_search: keyword match, fallback overlap scoring
  - RegulatoryRAG.search: offline-mode short-circuit (no Qdrant / OpenAI needed)

No Qdrant, no OpenAI, no fastembed required — all Qdrant I/O is exercised only
via the offline path or mocked ScoredPoint objects.
"""
from __future__ import annotations

import os
import types
from unittest.mock import MagicMock

import pytest

from aaa.agents.tier1.regulatory_rag import RegulatoryRAG, _point_to_hit


# ---------------------------------------------------------------------------
# Helpers — build a fake qdrant_client.ScoredPoint without importing qdrant
# ---------------------------------------------------------------------------

def _make_point(payload: dict, score: float = 0.85):
    """Return a lightweight object that mimics a Qdrant ScoredPoint."""
    pt = types.SimpleNamespace(payload=payload, score=score)
    return pt


# ---------------------------------------------------------------------------
# _point_to_hit — payload → contract mapping
# ---------------------------------------------------------------------------


class TestPointToHit:
    """Lock in the payload → {text, source, article, score} contract."""

    def test_eu_ai_act_full_payload(self):
        pt = _make_point({
            "text": "A provider shall establish a risk-management system.",
            "regulation": "EU_AI_Act",
            "ref": "Article 9",
            "kind": "article",
        }, score=0.92)
        hit = _point_to_hit(pt)
        assert hit["text"] == "A provider shall establish a risk-management system."
        assert hit["article"] == "Article 9"
        assert hit["source"] == "EU AI Act Article 9"
        assert hit["score"] == pytest.approx(0.92)

    def test_gdpr_regulation_label(self):
        pt = _make_point({
            "text": "Personal data shall be processed lawfully.",
            "regulation": "GDPR",
            "ref": "Article 5",
        }, score=0.75)
        hit = _point_to_hit(pt)
        assert hit["source"] == "GDPR Article 5"
        assert hit["article"] == "Article 5"

    def test_iso_42001_regulation_label(self):
        pt = _make_point({
            "text": "The organisation shall establish an AI management system.",
            "regulation": "ISO_IEC_42001",
            "ref": "4.1",
        }, score=0.60)
        hit = _point_to_hit(pt)
        assert hit["source"] == "ISO/IEC 42001 4.1"
        assert hit["article"] == "4.1"

    def test_missing_ref_falls_back_to_label_only(self):
        pt = _make_point({"text": "Some text.", "regulation": "EU_AI_Act"}, score=0.5)
        hit = _point_to_hit(pt)
        assert hit["source"] == "EU AI Act"
        assert hit["article"] == ""

    def test_unknown_regulation_uses_raw_key(self):
        pt = _make_point({"text": "X", "regulation": "MY_REG", "ref": "§3"}, score=0.1)
        hit = _point_to_hit(pt)
        assert hit["source"] == "MY_REG §3"

    def test_empty_payload_returns_safe_defaults(self):
        pt = _make_point({}, score=0.0)
        hit = _point_to_hit(pt)
        assert hit["text"] == ""
        assert hit["article"] == ""
        assert hit["score"] == pytest.approx(0.0)
        assert isinstance(hit["source"], str)

    def test_score_coerced_to_float(self):
        pt = _make_point({"regulation": "GDPR", "ref": "Recital 1"}, score=None)
        hit = _point_to_hit(pt)
        assert isinstance(hit["score"], float)
        assert hit["score"] == pytest.approx(0.0)

    def test_article_field_used_as_fallback_when_ref_absent(self):
        """Payload may use 'article' key instead of 'ref' (legacy compat)."""
        pt = _make_point({
            "text": "Fallback ref key.",
            "regulation": "EU_AI_Act",
            "article": "Article 13",
        }, score=0.7)
        hit = _point_to_hit(pt)
        assert hit["article"] == "Article 13"
        assert "Article 13" in hit["source"]


# ---------------------------------------------------------------------------
# RegulatoryRAG offline path (no network, no credentials)
# ---------------------------------------------------------------------------


@pytest.fixture
def offline_rag(monkeypatch):
    monkeypatch.setenv("AAA_OFFLINE_MODE", "true")
    return RegulatoryRAG()


class TestRegulatoryRAGOffline:
    """Verify the offline KB path works without any external dependencies."""

    def test_search_returns_list(self, offline_rag):
        hits = offline_rag.search("risk management system", top_k=3)
        assert isinstance(hits, list)

    def test_search_result_keys(self, offline_rag):
        hits = offline_rag.search("Article 9 risk management", top_k=1)
        assert hits, "Expected at least one offline hit"
        assert set(hits[0].keys()) >= {"text", "source", "article", "score"}

    def test_search_respects_top_k(self, offline_rag):
        hits = offline_rag.search("ai system transparency obligation", top_k=2)
        assert len(hits) <= 2

    def test_process_returns_string(self, offline_rag):
        import asyncio
        result = asyncio.run(offline_rag.process("risk management"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_no_match_returns_fallback(self, offline_rag):
        hits = offline_rag.search("zzzzznomatch12345", top_k=1)
        assert isinstance(hits, list)  # may be empty or lowest-score candidate
