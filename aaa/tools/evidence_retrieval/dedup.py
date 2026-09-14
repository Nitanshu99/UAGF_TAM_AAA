"""Finding F6 — retrieved evidence was neither de-duplicated nor re-ranked.

``acompletion_json_react`` accumulated hits with ``client_hits += new_client``
across every query of every round.  Each query runs independently against the
same collection, so a chunk that is relevant to three queries was injected three
times.  Case 01 call #004 carried **12 client-document hits comprising 4 unique
chunks** — 9,746 duplicated characters (~2,400 tokens) inside a 36,963-character
user message, roughly 34% waste.  Worse than the cost: chunks arrived in *query*
order, so the passage the retriever scored highest was not necessarily the one
the model read first.

Three properties, in this order:

*De-duplicated* on ``(source_uri, chunk_index, text)``.  The assessment named
``(source_uri, chunk_index)``, which is exactly right for client-document hits.
Regulatory hits have no ``chunk_index`` and their ``source_uri`` is a synthetic
pinpoint locator derived from the article ref, so two *different* passages of
Article 10 share one key — the text discriminates them, and identical text at
one locator is a duplicate by definition.  The highest-scoring copy of a
duplicate wins, because the same chunk legitimately scores differently against
different queries and the best score is what the re-rank should see.

*Re-ranked* by descending score, stably, so equal scores keep the order they
arrived in (seeded hits first).

*Capped* at one full round's worth of distinct material,
``_MAX_QUERIES_PER_KIND × _TOP_K``.  A derived bound rather than an invented
one: accumulation across rounds can no longer grow past what a single round
could ever have produced.

No absolute score floor is applied, and that is deliberate.  Scores are cosine
similarities from whichever embedding provider is configured, and the repo has
already been bitten by treating those as comparable across a provider swap
(``aaa.platform.embeddings.guard``).  A constant like ``score >= 0.2`` would
mean different things before and after such a swap and could silently empty the
evidence channel.  Ranking plus the cap bounds injection without a
scale-dependent constant: the weakest hits fall off the end of the list.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.evidence_retrieval.logger import _MAX_QUERIES_PER_KIND, _TOP_K

#: Most hits of one kind (regulatory or client-doc) that ever reach the model.
MAX_HITS_PER_KIND: int = _MAX_QUERIES_PER_KIND * _TOP_K


def _hit_key(hit: Any) -> tuple[Any, Any, Any]:
    """Identity of a retrieved chunk for de-duplication purposes."""
    if not isinstance(hit, dict):
        return (repr(hit), None, None)
    return (hit.get("source_uri") or hit.get("locator") or "",
            hit.get("chunk_index"), hit.get("text"))


def _hit_score(hit: Any) -> float:
    """Retrieval score of *hit*; absent or unparsable scores rank last."""
    try:
        return float(hit.get("score") or 0.0) if isinstance(hit, dict) else 0.0
    except (TypeError, ValueError):
        return 0.0


def hit_keys(hits: list[Any]) -> set[tuple[Any, Any, Any]]:
    """The identities in *hits*, on the same key ``merge_hits`` de-duplicates by.

    Fix 18's productivity gate asks whether a round put anything new in front of
    the model. Length cannot answer that — at the cap a round may displace a
    weaker hit without growing the list, which is new evidence, and it may
    return a dozen duplicates, which is not.

    :param hits: Retrieved chunks.
    :returns: One key per distinct chunk.
    """
    return {_hit_key(hit) for hit in hits}


def merge_hits(existing: list[Any], new: list[Any], *,
               cap: int = MAX_HITS_PER_KIND) -> tuple[list[Any], int, int]:
    """Fold *new* hits into *existing*, de-duplicated, re-ranked and capped.

    :param existing: Hits already in the payload (seeded, or from earlier rounds).
    :param new: Hits this round's queries returned.
    :param cap: Maximum hits to keep after ranking.
    :returns: ``(merged, duplicates_dropped, over_cap_dropped)``.
    """
    best: dict[tuple[Any, Any, Any], Any] = {}
    duplicates = 0
    for hit in [*existing, *new]:
        key = _hit_key(hit)
        seen = best.get(key)
        if seen is None:
            best[key] = hit
            continue
        duplicates += 1
        if _hit_score(hit) > _hit_score(seen):
            best[key] = hit
    ranked = sorted(best.values(), key=_hit_score, reverse=True)
    return ranked[:cap], duplicates, max(0, len(ranked) - cap)


__all__ = ["MAX_HITS_PER_KIND", "hit_keys", "merge_hits"]
