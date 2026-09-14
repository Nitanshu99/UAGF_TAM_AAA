"""Cross-encoder re-ranking: judge relevance, never edit the text.

RRF fuses two bi-encoder rankings, neither of which reads the query and the
chunk together, and three chunks then survived out of 64 prefetched with
nothing having judged whether any was on point. These tests pin the promotion,
the annotation, the visibility of what was passed over, and — most of it — the
degraded paths, because a retrieval stage that fails must fail into the old
ordering rather than into no evidence.

The encoder is injected throughout: the suite must not download a model. One
integration test drives the real one, gated behind ``AAA_RERANK_INTEGRATION=1``.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import pytest

from aaa.agents.tier1.regulatory_rag import RegulatoryRAG
from aaa.agents.tier1.regulatory_rag import rerank as rr
from aaa.agents.tier1.regulatory_rag.rerank import encoder as rr_encoder
from aaa.agents.tier1.regulatory_rag.rerank import scoring as rr_scoring

#: The on-point passage sits 4th, where a `top_k` of 3 could never reach it.
_CANDIDATES: list[dict[str, Any]] = [
    {"ref": "Recital 60", "text": "Providers should consider the intended purpose.",
     "score": 0.51, "locator": "euaiact://Recital_60"},
    {"ref": "Article 4", "text": "Providers shall ensure a sufficient level of AI literacy.",
     "score": 0.48, "locator": "euaiact://Article_4"},
    {"ref": "Article 50", "text": "Systems interacting with people shall disclose it.",
     "score": 0.45, "locator": "euaiact://Article_50"},
    {"ref": "Article 10", "text": "Training, validation and testing data sets shall be "
                                  "relevant and sufficiently representative.",
     "score": 0.42, "locator": "euaiact://Article_10"},
    {"ref": "Annex III", "text": "High-risk areas include biometrics and education.",
     "score": 0.40, "locator": "euaiact://Annex_III"},
]

_QUERY = "Article 10 training data quality"


class _Encoder:
    """Scores by ``ref`` → logit, so a test states the ranking it wants."""

    def __init__(self, logits: dict[str, float], fail: bool = False):
        self._logits, self._fail = logits, fail
        self.calls: list[tuple[str, int]] = []

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """Mimic ``fastembed.TextCrossEncoder.rerank``."""
        self.calls.append((query, len(documents)))
        if self._fail:
            raise RuntimeError("onnx session died")
        out = []
        for doc in documents:
            match = next((r for r, _ in self._logits.items() if r in doc), None)
            out.append(self._logits.get(match, -8.0) if match else -8.0)
        return out


def _encoder(**by_text: float) -> _Encoder:
    return _Encoder(by_text)


# --------------------------------------------------------------------------- #
# the promotion — what the pool is for
# --------------------------------------------------------------------------- #

def test_the_on_point_passage_outside_top_k_is_promoted():
    """RRF put Article 10 fourth; at top_k=3 it was simply unreachable."""
    assert [h["ref"] for h in _CANDIDATES[:3]] == ["Recital 60", "Article 4", "Article 50"]

    out = rr.rerank(_QUERY, _CANDIDATES, 3, encoder=_encoder(Training=3.0, literacy=-2.0))
    assert out[0]["ref"] == "Article 10"


def test_the_whole_pool_is_scored_not_just_the_survivors():
    """Re-ranking a top_k already cut by RRF would recover nothing."""
    enc = _encoder(Training=3.0)
    rr.rerank(_QUERY, _CANDIDATES, 3, encoder=enc)
    assert enc.calls == [(_QUERY, 5)]


def test_search_pulls_a_pool_and_returns_top_k(monkeypatch):
    """`search` must widen at retrieval and narrow after judging, not before."""
    seen: dict = {}

    def _fake_vector(self, query: str, top_k: int) -> list[dict[str, Any]]:
        seen["asked_for"] = top_k
        return list(_CANDIDATES)

    monkeypatch.setattr(RegulatoryRAG, "_vector_search", _fake_vector)
    monkeypatch.setattr(rr, "_get_encoder", lambda: _encoder(Training=3.0))

    hits = RegulatoryRAG().search(_QUERY, top_k=3)
    assert seen["asked_for"] == rr.CANDIDATE_POOL, "retrieval still pulled only top_k"
    assert len(hits) == 3
    assert hits[0]["ref"] == "Article 10"


def test_a_top_k_larger_than_the_pool_is_honoured(monkeypatch):
    """The pool is a floor on retrieval breadth, not a ceiling on the answer."""
    seen: dict = {}

    def _fake_vector(self, query: str, top_k: int) -> list[dict[str, Any]]:
        seen["asked_for"] = top_k
        return list(_CANDIDATES)

    monkeypatch.setattr(RegulatoryRAG, "_vector_search", _fake_vector)
    monkeypatch.setattr(rr, "_get_encoder", lambda: None)
    RegulatoryRAG().search(_QUERY, top_k=40)
    assert seen["asked_for"] == 40


# --------------------------------------------------------------------------- #
# the annotation — and the text it must not touch
# --------------------------------------------------------------------------- #

def test_the_chunk_text_is_never_edited():
    """'Verbatim' is structural here: selection cannot rewrite a quotation."""
    out = rr.rerank(_QUERY, _CANDIDATES, 5, encoder=_encoder(Training=3.0))
    assert {h["text"] for h in out} == {c["text"] for c in _CANDIDATES}


def test_the_input_hits_are_not_mutated():
    """Callers keep their own list; re-ranking returns new dicts."""
    rr.rerank(_QUERY, _CANDIDATES, 3, encoder=_encoder(Training=3.0))
    assert _CANDIDATES[3]["score"] == 0.42, "the caller's hit was rewritten in place"
    assert "relevant" not in _CANDIDATES[3]


def test_each_hit_carries_its_judgement_and_its_old_score():
    """The annotation is the point; losing the retrieval score hides the change."""
    out = rr.rerank(_QUERY, _CANDIDATES, 2, encoder=_encoder(Training=3.0))
    top = out[0]
    assert top["retrieval_score"] == 0.42, "the bi-encoder score is kept, not discarded"
    assert top["rerank_score"] == 3.0
    assert top["rerank_position"] == 1
    assert top["relevant"] is True
    assert 0.9 < top["score"] < 1.0, "score carries the normalised re-ranked value"


def test_the_relevance_boundary_is_the_models_own_and_not_a_tuning_constant():
    """A binary-relevance cross-encoder separates at logit 0 → sigmoid 0.5.

    This is why a threshold is defensible here when fix 9 refused one: it does
    not move when the *embedding* provider does.
    """
    assert rr_scoring._normalise(0.0) == pytest.approx(rr_scoring.RELEVANT_ABOVE)
    out = rr.rerank(_QUERY, _CANDIDATES, 5, encoder=_encoder(Training=0.01, literacy=-0.01))
    verdicts = {h["ref"]: h["relevant"] for h in out}
    assert verdicts["Article 10"] is True
    assert verdicts["Article 4"] is False


def test_normalisation_is_bounded_against_extreme_logits():
    """An overflow in the ranking stage must not take the phase with it."""
    assert 0.0 <= rr_scoring._normalise(-900.0) < 0.001
    assert 0.999 < rr_scoring._normalise(900.0) <= 1.0


# --------------------------------------------------------------------------- #
# visibility — a drop nobody can see is worse than noise
# --------------------------------------------------------------------------- #

def test_what_was_passed_over_is_recorded(caplog):
    """A filtered-out passage must be visible in the trail, not merely absent."""
    with caplog.at_level(logging.INFO):
        rr.rerank(_QUERY, _CANDIDATES, 2, encoder=_encoder(Training=3.0))
    assert "Not passed" in caplog.text
    assert "Article 50" in caplog.text
    assert "not absent from the corpus" in caplog.text


def test_a_pool_with_nothing_relevant_says_so(caplog):
    """The passages are still returned; the conclusion drawn is what changes."""
    with caplog.at_level(logging.WARNING):
        out = rr.rerank(_QUERY, _CANDIDATES, 3, encoder=_encoder())
    assert len(out) == 3, "returned anyway — the reader decides, not the ranker"
    assert all(h["relevant"] is False for h in out)
    assert "scored above the relevance boundary" in caplog.text


# --------------------------------------------------------------------------- #
# degraded paths — ranking must never cost the evidence
# --------------------------------------------------------------------------- #

def test_no_encoder_keeps_the_rrf_order(monkeypatch):
    """Absent the model, behaviour is exactly what it was before this stage."""
    monkeypatch.setattr(rr, "_get_encoder", lambda: None)
    out = rr.rerank(_QUERY, _CANDIDATES, 3)
    assert [h["ref"] for h in out] == ["Recital 60", "Article 4", "Article 50"]
    assert "relevant" not in out[0], "unjudged hits must not look judged"


def test_a_raising_encoder_keeps_the_rrf_order(caplog):
    """An ONNX failure mid-run degrades the ranking, never the retrieval."""
    with caplog.at_level(logging.WARNING):
        out = rr.rerank(_QUERY, _CANDIDATES, 3, encoder=_Encoder({}, fail=True))
    assert [h["ref"] for h in out] == ["Recital 60", "Article 4", "Article 50"]
    assert "keeping RRF order" in caplog.text


def test_an_unimportable_encoder_is_reported_once_then_remembered(caplog, monkeypatch):
    """The import is attempted once, not per query — and it is never silent."""
    monkeypatch.setattr(rr_encoder, "_ENCODER", None)
    monkeypatch.setattr(rr_encoder, "_UNAVAILABLE", False)
    monkeypatch.setitem(__import__("sys").modules, "fastembed.rerank.cross_encoder", None)

    with caplog.at_level(logging.WARNING):
        assert rr._get_encoder() is None
    assert "re-ranking unavailable" in caplog.text
    assert "falling back to RRF order" in caplog.text

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert rr._get_encoder() is None
    assert caplog.text == "", "a second query must not retry the import"


def test_empty_and_degenerate_inputs():
    """No hits, or no room for them, is not an error."""
    assert rr.rerank(_QUERY, [], 3, encoder=_encoder()) == []
    assert rr.rerank(_QUERY, _CANDIDATES, 0, encoder=_encoder()) == []


def test_the_builtin_fallback_is_reranked_too(monkeypatch):
    """Offline must not mean unjudged; both retrieval paths feed one ranker."""
    def _boom(self, query: str, top_k: int) -> list[dict[str, Any]]:
        raise RuntimeError("qdrant unreachable")

    monkeypatch.setattr(RegulatoryRAG, "_vector_search", _boom)
    monkeypatch.setattr(RegulatoryRAG, "_builtin_search",
                        staticmethod(lambda q, k: list(_CANDIDATES)))
    monkeypatch.setattr(rr, "_get_encoder", lambda: _encoder(Training=3.0))
    assert RegulatoryRAG().search(_QUERY, top_k=1)[0]["ref"] == "Article 10"


# --------------------------------------------------------------------------- #
# the real model, on request
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(os.environ.get("AAA_RERANK_INTEGRATION") != "1",
                    reason="downloads a model; set AAA_RERANK_INTEGRATION=1 to run")
def test_the_real_cross_encoder_promotes_the_right_article():
    """The fakes state a ranking; this one earns it."""
    out = rr.rerank("Article 10 training data quality and representativeness",
                   _CANDIDATES, 3)
    assert out[0]["ref"] == "Article 10"
    assert out[0]["relevant"] is True
    assert all(h["relevant"] is False for h in out[1:])
