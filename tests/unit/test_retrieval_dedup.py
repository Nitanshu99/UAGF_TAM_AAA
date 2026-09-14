"""Fix 9 / finding F6 — retrieved chunks are de-duplicated, re-ranked and capped.

Case 01 call #004 injected 12 client-document hits comprising 4 unique chunks —
9,746 duplicated characters, ~34% of the retrieved payload — because
``acompletion_json_react`` accumulated ``hits += new_hits`` across queries that
each matched the same material.  Chunks also arrived in query order rather than
score order, so the best-scoring passage was not necessarily read first.
"""
from __future__ import annotations

import asyncio

from aaa.tools.evidence_retrieval import MAX_HITS_PER_KIND, acompletion_json_react, merge_hits
from aaa.tools.evidence_retrieval.logger import _MAX_QUERIES_PER_KIND, _TOP_K


def _chunk(uri: str, index: int, score: float, text: str = "body") -> dict:
    return {"source_uri": uri, "chunk_index": index, "score": score, "text": text}


# --------------------------------------------------------------------------
# merge_hits — de-duplication
# --------------------------------------------------------------------------
def test_the_same_chunk_matched_by_three_queries_is_injected_once():
    """The exact shape of F6: one chunk, three query matches, one injection."""
    rmf = _chunk("minio://risk_management_file.txt", 0, 0.399)
    merged, duplicates, _ = merge_hits([], [rmf, dict(rmf), dict(rmf)])

    assert len(merged) == 1
    assert duplicates == 2


def test_case_01_call_004_twelve_hits_collapse_to_four():
    """The assessed payload verbatim: 12 client_doc_hits, 4 unique chunks."""
    rmf0, rmf1 = "minio://risk_management_file.txt", "minio://risk_management_file.txt"
    pmm, doc = "minio://post_market_monitoring_plan.txt", "minio://eu_declaration.txt"
    assessed = [
        _chunk(rmf0, 0, 0.39905977), _chunk(pmm, 0, 0.39650166),
        _chunk(rmf1, 1, 0.34951818), _chunk(rmf1, 1, 0.36068636),
        _chunk(rmf0, 0, 0.33182952), _chunk(pmm, 0, 0.3273725),
        _chunk(rmf0, 0, 0.28103662), _chunk(pmm, 0, 0.2526192),
        _chunk(doc, 0, 0.2007971), _chunk(doc, 0, 0.42714876),
        _chunk(rmf0, 0, 0.36537606), _chunk(pmm, 0, 0.32754532),
    ]
    merged, duplicates, _ = merge_hits([], assessed)

    assert len(merged) == 4, "12 hits for 4 unique chunks (F6)"
    assert duplicates == 8


def test_the_highest_scoring_copy_of_a_duplicate_wins():
    """The same chunk scores differently per query; the re-rank sees its best."""
    low = _chunk("minio://rmf.txt", 1, 0.34951818)
    high = _chunk("minio://rmf.txt", 1, 0.36068636)
    merged, _, _ = merge_hits([], [low, high])

    assert merged[0]["score"] == 0.36068636


def test_distinct_chunks_of_one_document_are_not_collapsed():
    """`chunk_index` discriminates: two passages of one file are two passages."""
    merged, duplicates, _ = merge_hits(
        [], [_chunk("minio://rmf.txt", 0, 0.4, "a"), _chunk("minio://rmf.txt", 1, 0.3, "b")])

    assert len(merged) == 2
    assert duplicates == 0


def test_regulatory_passages_sharing_a_locator_are_kept_apart_by_text():
    """Regulatory hits have no chunk_index and one locator per article ref."""
    art10 = {"source_uri": "euaiact://Article_10", "score": 0.9}
    merged, _, _ = merge_hits([], [{**art10, "text": "para 2"}, {**art10, "text": "para 3"}])

    assert len(merged) == 2, "two passages of one article are not one passage"


def test_an_identical_regulatory_passage_is_still_a_duplicate():
    art10 = {"source_uri": "euaiact://Article_10", "score": 0.9, "text": "para 2"}
    merged, duplicates, _ = merge_hits([], [art10, dict(art10)])

    assert (len(merged), duplicates) == (1, 1)


# --------------------------------------------------------------------------
# merge_hits — ranking and cap
# --------------------------------------------------------------------------
def test_hits_are_ranked_by_descending_score():
    merged, _, _ = merge_hits(
        [], [_chunk("a://1", 0, 0.20, "a"), _chunk("b://1", 0, 0.42, "b"),
             _chunk("c://1", 0, 0.31, "c")])

    assert [h["score"] for h in merged] == [0.42, 0.31, 0.20]


def test_equal_scores_keep_arrival_order():
    """Stable sort: seeded hits are not shuffled behind later arrivals."""
    seed = _chunk("seed://1", 0, 0.5, "seed")
    later = _chunk("later://1", 0, 0.5, "later")
    merged, _, _ = merge_hits([seed], [later])

    assert [h["text"] for h in merged] == ["seed", "later"]


def test_a_hit_without_a_score_ranks_last_rather_than_raising():
    merged, _, _ = merge_hits([], [{"source_uri": "no-score://1", "text": "x"},
                                   _chunk("scored://1", 0, 0.1, "y")])

    assert [h["text"] for h in merged] == ["y", "x"]


def test_a_non_numeric_score_does_not_raise():
    merged, _, _ = merge_hits([], [{"source_uri": "bad://1", "score": "high", "text": "x"}])

    assert len(merged) == 1


def test_injection_is_capped_at_one_rounds_worth_of_distinct_material():
    """The cap is derived, not invented: max queries × top_k."""
    assert MAX_HITS_PER_KIND == _MAX_QUERIES_PER_KIND * _TOP_K

    many = [_chunk(f"uri://{i}", 0, i / 100, f"t{i}") for i in range(MAX_HITS_PER_KIND + 5)]
    merged, _, over_cap = merge_hits([], many)

    assert len(merged) == MAX_HITS_PER_KIND
    assert over_cap == 5


def test_the_cap_keeps_the_best_scoring_hits():
    many = [_chunk(f"uri://{i}", 0, i / 100, f"t{i}") for i in range(MAX_HITS_PER_KIND + 3)]
    merged, _, _ = merge_hits([], many)

    dropped = {f"t{i}" for i in range(3)}
    assert dropped.isdisjoint({h["text"] for h in merged}), "the weakest hits fall off"


def test_a_non_dict_hit_is_tolerated():
    merged, _, _ = merge_hits([], ["a stray string", "a stray string"])

    assert len(merged) == 1


# --------------------------------------------------------------------------
# The loop end to end
# --------------------------------------------------------------------------
class _DuplicatingRag:
    """Every query returns the same chunk — the F6 condition."""

    def search(self, query, top_k=3):  # noqa: ARG002
        return [{"source_uri": "euaiact://Article_10", "chunk_index": 0,
                 "text": "Article 10 …", "score": 0.4}] * top_k


def test_the_loop_injects_each_chunk_once_however_many_queries_matched_it():
    seen: list[dict] = []

    class _Agent:
        name = "Fake"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            seen.append(payload)
            type(self).calls += 1
            if type(self).calls == 1:
                return {"retrieval_plan": {
                    "regulatory_queries": ["Article 10 data governance",
                                           "Article 10 paragraph 5",
                                           "Article 10 paragraph 3"],
                    "client_doc_queries": []}}
            return {"done": True}

    asyncio.run(acompletion_json_react(
        _Agent(), "phase2_data", {}, rag=_DuplicatingRag(), engagement_id="", rounds=1))

    injected = seen[-1]["regulatory_hits"]
    assert len(injected) == 1, (
        f"3 queries × top_k 3 injected {len(injected)} copies of one chunk (F6)")


def test_seeded_hits_are_ranked_before_the_first_expansion():
    seen: list[dict] = []

    class _Agent:
        name = "Fake"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            seen.append(payload)
            type(self).calls += 1
            if type(self).calls == 1:
                return {"retrieval_plan": {"regulatory_queries": ["q"],
                                           "client_doc_queries": []}}
            return {"done": True}

    seeds = [_chunk("seed://low", 0, 0.1, "low"), _chunk("seed://high", 0, 0.9, "high")]
    asyncio.run(acompletion_json_react(
        _Agent(), "phase2_data", {"regulatory_hits": seeds},
        rag=_DuplicatingRag(), engagement_id="", rounds=1))

    assert seen[-1]["regulatory_hits"][0]["text"] == "high"
