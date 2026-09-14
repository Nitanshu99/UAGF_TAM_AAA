"""Fetching a cited article by identifier rather than by similarity (fix 16, P1).

The post-fix run's Verifier asked the corpus ``f"{ref} EU AI Act"`` for every
citation it checked. Of fifteen distinct queries, one returned its own
reference: ``Article 72 EU AI Act`` came back with Articles 74 and 71, and the
article the assessed run had called fictional was still not being shown to the
agent judging it. ``ref`` is an indexed keyword field in the corpus payload, so
the question has an exact answer; these tests pin that it is asked that way, and
that a search result standing in for a missing unit travels labelled as one.
"""
from __future__ import annotations

import logging
from typing import Any

import pytest

from aaa.agents.tier1.regulatory_rag.agent import RegulatoryRAG
from aaa.agents.tier1.regulatory_rag.hits import _point_to_hit
from aaa.agents.tier1.regulatory_rag.lookup import _kb_ref, kb_lookup
from aaa.agents.tier1.verifier.citations import retrieve_cited_law

#: What "Article 72 EU AI Act" actually retrieved in the post-fix run.
_NEIGHBOURS = {"Article 72": ["Article 74", "Article 71"],
               "Article 10": ["Recital 94", "Recital 39"]}


class _Record:
    """A Qdrant scroll record — payload, no score."""

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload


class _Qdrant:
    """In-memory corpus with the real payload shape and a filtering scroll."""

    def __init__(self, refs: tuple[str, ...] = ("Article 10", "Article 72", "Annex III")):
        self.filters: list[dict[str, Any]] = []
        self.points = [
            _Record({"regulation": "EU_AI_Act", "ref": ref, "kind": "article",
                     "title": f"{ref} heading", "source_file": "EU_AI_Act.html",
                     "chunk_index": i, "chunk_total": 2,
                     "text": f"{ref} operative text, chunk {i}."})
            # stored second chunk first, so ordering has to be done by the code
            for ref in refs for i in (1, 0)
        ] + [
            _Record({"regulation": "GDPR", "ref": "Article 10", "kind": "article",
                     "title": "Criminal convictions", "source_file": "GDPR.html",
                     "chunk_index": 0, "chunk_total": 1,
                     "text": "GDPR Article 10 — criminal conviction data."})
        ]

    def scroll(self, collection_name, scroll_filter, limit, with_payload):
        """Match every payload field the filter names, exactly."""
        want = {c.key: c.match.value for c in scroll_filter.must}
        self.filters.append(want)
        found = [p for p in self.points
                 if all(p.payload.get(k) == v for k, v in want.items())]
        return found[:limit], None


class _SearchOnlyRag:
    """The pre-fix channel: semantic search, no identifier lookup."""

    def __init__(self, neighbours: dict[str, list[str]] | None = None):
        self.queries: list[str] = []
        self._near = _NEIGHBOURS if neighbours is None else neighbours

    def search(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Return P1's real neighbours for the bare-label query."""
        self.queries.append(query)
        ref = query.replace(" EU AI Act", "")
        return [{"text": f"{r} text", "ref": r, "article": r, "score": 0.99,
                 "source_uri": f"euaiact://{r.replace(' ', '_')}"}
                for r in self._near.get(ref, [])][:top_k]


def _rag(corpus: _Qdrant | None = None, **kw) -> RegulatoryRAG:
    """A RegulatoryRAG whose Qdrant is the in-memory corpus and whose search stubs P1."""
    rag = RegulatoryRAG()
    rag._qdrant = corpus if corpus is not None else _Qdrant()
    stub = _SearchOnlyRag(**kw)
    rag.search = stub.search  # type: ignore[method-assign]
    rag.searched = stub.queries  # type: ignore[attr-defined]
    return rag


# --------------------------------------------------------------------------- #
# the lookup itself
# --------------------------------------------------------------------------- #

def test_a_cited_article_is_fetched_by_its_own_ref():
    """`Article 72` returns Article 72 — the query that returned 74 and 71."""
    hits = _rag().lookup("Article 72", top_k=2)
    assert [h["ref"] for h in hits] == ["Article 72", "Article 72"]


def test_the_lookup_filters_on_ref_and_regulation():
    """A bare ref would match GDPR too; the filter names both fields."""
    corpus = _Qdrant()
    _rag(corpus).lookup("Article 10")
    assert corpus.filters == [{"ref": "Article 10", "regulation": "EU_AI_Act"}]


def test_gdpr_does_not_answer_an_eu_ai_act_citation():
    """GDPR Article 10 exists and must not be returned for an AI Act citation."""
    hits = _rag().lookup("Article 10", top_k=4)
    assert hits and not any("GDPR" in h["text"] for h in hits)


def test_chunks_come_back_in_article_order_not_storage_order():
    """An article opens with its operative rule; a citation check wants the start."""
    assert [h["chunk_index"] for h in _rag().lookup("Article 10", top_k=2)] == [0, 1]


def test_a_lookup_hit_is_labelled_as_an_identifier_match():
    """`match` is what lets the Verifier tell the article from something near it."""
    hit = _rag().lookup("Article 72", top_k=1)[0]
    assert hit["match"] == "ref_lookup" and hit["lookup_ref"] == "Article 72"
    assert hit["score"] == 1.0 and hit["relevant"] is True


def test_an_absent_unit_returns_nothing_rather_than_something_near_it():
    """Empty is the meaningful answer: the corpus holds no unit under that ref."""
    assert _rag().lookup("Article 99") == []


@pytest.mark.parametrize("bad", ["", "   "])
def test_an_empty_ref_is_not_asked(bad):
    """No query is worth making for a reference the artefact did not give."""
    corpus = _Qdrant()
    assert _rag(corpus).lookup(bad) == [] and not corpus.filters


def test_chunk_index_is_surfaced_on_corpus_hits():
    """merge_hits keys on it, and the lookup orders on it."""
    point = _Record({"regulation": "EU_AI_Act", "ref": "Article 10", "chunk_index": 3,
                     "text": "t", "source_file": "f.html"})
    assert _point_to_hit(point)["chunk_index"] == 3


# --------------------------------------------------------------------------- #
# the degraded path
# --------------------------------------------------------------------------- #

def test_the_builtin_kb_answers_the_same_question_in_its_own_spelling():
    """The KB refs `Art.10`/`Annex_III` where the corpus says `Article 10`."""
    assert _kb_ref("Article 10") == "Art.10"
    assert _kb_ref("Annex III") == "Annex_III"
    assert kb_lookup("Article 10", top_k=1)[0]["match"] == "ref_lookup"


class _DeadQdrant:
    """A corpus that cannot be scrolled."""

    def scroll(self, **_kw):
        """Fail the way an unreachable corpus does."""
        raise ConnectionError("qdrant unreachable")


def test_an_unreachable_corpus_falls_back_to_the_kb(caplog):
    """Qdrant down must not silently turn a lookup into a search."""
    with caplog.at_level(logging.WARNING):
        hits = _rag(_DeadQdrant()).lookup("Article 10", top_k=1)
    assert hits and hits[0]["match"] == "ref_lookup"
    assert "falling back to" in caplog.text


# --------------------------------------------------------------------------- #
# what the Verifier is handed
# --------------------------------------------------------------------------- #

def test_the_citation_channel_now_retrieves_the_article_it_names():
    """P1's headline: the reference resolves to itself, not to its neighbours."""
    hits = retrieve_cited_law(_rag(), {"cites": "Article 72"}, top_k=2)
    assert {h["ref"] for h in hits} == {"Article 72"}
    assert all(h["match"] == "ref_lookup" for h in hits)


def test_search_is_not_consulted_when_the_lookup_answers():
    """The semantic channel is the fallback, not a second opinion blended in."""
    rag = _rag()
    retrieve_cited_law(rag, {"cites": "Article 72"}, top_k=2)
    assert not rag.searched


def test_a_missing_unit_falls_back_to_search_and_says_so(caplog):
    """The fix order asks for the fallback; the label keeps it honest."""
    rag = _rag(neighbours={"Article 99": ["Article 98"]})
    with caplog.at_level(logging.INFO):
        hits = retrieve_cited_law(rag, {"cites": "Art. 99"}, top_k=2)
    assert rag.searched == ["Article 99 EU AI Act"]
    assert [(h["ref"], h["match"]) for h in hits] == [("Article 98", "semantic_fallback")]
    assert "cannot confirm the reference" in caplog.text


def test_a_retriever_without_a_lookup_is_not_reported_as_a_failure(caplog):
    """A stub or an older retriever degrades to search without a false alarm."""
    rag = _SearchOnlyRag()
    with caplog.at_level(logging.WARNING):
        hits = retrieve_cited_law(rag, {"cites": "Article 72"}, top_k=2)
    assert all(h["match"] == "semantic_fallback" for h in hits)
    assert "failed" not in caplog.text


def test_a_raising_lookup_does_not_fail_the_critique(caplog):
    """Retrieval is best-effort; the critique still happens."""
    class _Boom(_SearchOnlyRag):
        """A retriever whose lookup raises."""

        def lookup(self, ref, top_k=2):
            """Fail the way an unreachable corpus does."""
            raise RuntimeError("qdrant down")

    with caplog.at_level(logging.WARNING):
        hits = retrieve_cited_law(_Boom(), {"cites": "Article 72"}, top_k=2)
    assert [h["match"] for h in hits] == ["semantic_fallback"] * len(hits)
    assert "citation lookup failed" in caplog.text


def test_the_article_itself_outranks_a_passage_that_merely_resembles_it():
    """merge_hits ranks on score, and an exact match is scored above a guess."""
    rag = _rag(neighbours={"Article 10": ["Recital 94"]})
    hits = retrieve_cited_law(rag, {"cites": "Art. 10 and Art. 99"}, top_k=2)
    assert hits[0]["match"] == "ref_lookup" and hits[0]["ref"] == "Article 10"


def test_the_prompt_tells_the_model_how_to_read_the_label():
    """A field the model is never told about is a field it cannot use."""
    from aaa.platform.prompt_registry import load_prompt
    prompt = load_prompt("verifier")
    assert "ref_lookup" in prompt and "semantic_fallback" in prompt
    assert "NOT the cited article" in prompt
