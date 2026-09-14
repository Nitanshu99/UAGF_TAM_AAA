"""_point_to_hit edge cases: score coercion and legacy 'article' key."""
from __future__ import annotations

import types

import pytest

from aaa.agents.tier1.regulatory_rag import _point_to_hit


def _make_point(payload: dict, score: float = 0.85):
    return types.SimpleNamespace(payload=payload, score=score)


def test_score_coerced_to_float():
    hit = _point_to_hit(_make_point({"regulation": "GDPR", "ref": "Recital 1"},
                                    score=None))
    assert isinstance(hit["score"], float)
    assert hit["score"] == pytest.approx(0.0)


def test_article_field_used_as_fallback_when_ref_absent():
    """Payload may use 'article' key instead of 'ref' (legacy compat)."""
    hit = _point_to_hit(_make_point({
        "text": "Fallback ref key.", "regulation": "EU_AI_Act",
        "article": "Article 13",
    }, score=0.7))
    assert hit["article"] == "Article 13"
    assert "Article 13" in hit["source"]
