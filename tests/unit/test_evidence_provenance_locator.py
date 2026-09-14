"""Regulatory-locator enrichment on RAG hits."""
from __future__ import annotations

from aaa.agents.tier1.regulatory_rag import _locator, _point_to_hit
from aaa.tools.evidence_retrieval import seed_regulatory_hits


class _Pt:
    def __init__(self, payload, score=0.5):
        self.payload = payload
        self.score = score


def test_point_to_hit_exposes_locator_and_obligations():
    hit = _point_to_hit(_Pt({
        "text": "…", "regulation": "EU_AI_Act", "ref": "Article 10",
        "title": "Data and data governance", "source_file": "eu_ai_act.md",
        "obligations": ["data_quality"],
    }))
    assert hit["locator"] == "euaiact://Article_10#eu_ai_act.md"
    assert hit["source_uri"] == hit["locator"]
    assert hit["obligations"] == ["data_quality"]
    assert hit["ref"] == "Article 10"


def test_locator_helper_scheme_by_regulation():
    assert _locator("EU_AI_Act", "Article 9") == "euaiact://Article_9"
    assert _locator("GDPR", "Article 5") == "gdpr://Article_5"
    assert _locator("EU_AI_Act", "") == ""


def test_seed_regulatory_hits_fallback_have_locator(monkeypatch):
    from aaa.agents.tier1.regulatory_rag import RegulatoryRAG
    rag = RegulatoryRAG()
    monkeypatch.setattr(
        rag, "_vector_search",
        lambda query, top_k: (_ for _ in ()).throw(ConnectionError("no qdrant")),
    )
    hits = seed_regulatory_hits(rag, "risk management", top_k=1)
    assert hits and hits[0]["source_uri"].startswith("euaiact://")


def test_seed_regulatory_hits_none_rag_is_safe():
    assert seed_regulatory_hits(None, "anything") == []
