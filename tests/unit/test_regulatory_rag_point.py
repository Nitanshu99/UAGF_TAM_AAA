"""_point_to_hit: payload → {text, source, article, score} contract.

No Qdrant, no OpenAI, no fastembed — ScoredPoints are mocked with
SimpleNamespace.
"""
from __future__ import annotations

import types

import pytest

from aaa.agents.tier1.regulatory_rag import _point_to_hit


def _make_point(payload: dict, score: float = 0.85):
    """Return a lightweight object that mimics a Qdrant ScoredPoint."""
    return types.SimpleNamespace(payload=payload, score=score)


class TestPointToHit:
    """Lock in the payload → {text, source, article, score} contract."""

    def test_eu_ai_act_full_payload(self):
        hit = _point_to_hit(_make_point({
            "text": "A provider shall establish a risk-management system.",
            "regulation": "EU_AI_Act", "ref": "Article 9", "kind": "article",
        }, score=0.92))
        assert hit["text"] == "A provider shall establish a risk-management system."
        assert hit["article"] == "Article 9"
        assert hit["source"] == "EU AI Act Article 9"
        assert hit["score"] == pytest.approx(0.92)

    def test_gdpr_regulation_label(self):
        hit = _point_to_hit(_make_point({
            "text": "Personal data shall be processed lawfully.",
            "regulation": "GDPR", "ref": "Article 5",
        }, score=0.75))
        assert hit["source"] == "GDPR Article 5"
        assert hit["article"] == "Article 5"

    def test_iso_42001_regulation_label(self):
        hit = _point_to_hit(_make_point({
            "text": "The organisation shall establish an AI management system.",
            "regulation": "ISO_IEC_42001", "ref": "4.1",
        }, score=0.60))
        assert hit["source"] == "ISO/IEC 42001 4.1"
        assert hit["article"] == "4.1"

    def test_missing_ref_falls_back_to_label_only(self):
        hit = _point_to_hit(_make_point(
            {"text": "Some text.", "regulation": "EU_AI_Act"}, score=0.5))
        assert hit["source"] == "EU AI Act"
        assert hit["article"] == ""

    def test_unknown_regulation_uses_raw_key(self):
        hit = _point_to_hit(_make_point(
            {"text": "X", "regulation": "MY_REG", "ref": "§3"}, score=0.1))
        assert hit["source"] == "MY_REG §3"

    def test_empty_payload_returns_safe_defaults(self):
        hit = _point_to_hit(_make_point({}, score=0.0))
        assert hit["text"] == ""
        assert hit["article"] == ""
        assert hit["score"] == pytest.approx(0.0)
        assert isinstance(hit["source"], str)
