"""The two retrieval entry points every phase agent calls: similarity search, and ref lookup."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.regulatory_rag.lookup import DEFAULT_REGULATION
from aaa.agents.tier1.regulatory_rag.rerank import CANDIDATE_POOL, rerank

logger = logging.getLogger(__name__)



def search(self: "Any", query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Search the corpus for passages relevant to *query*.

    Two stages. Retrieval pulls a pool of :data:`CANDIDATE_POOL` candidates
    — hybrid dense + sparse, RRF-fused — and a cross-encoder then reads each
    against the query and keeps the best ``top_k``. The pool is what buys
    the recall: returning ``top_k`` straight from RRF made a passage ranked
    just outside it unreachable, with nothing having judged whether the ones
    that did survive were on point.

    Chunk text is never edited by either stage; re-ranking selects and
    annotates, so what an agent quotes is what the corpus holds.

    :param query: Free-text question or keyword string.
    :type query: str
    :param top_k: Maximum number of results to return.
    :type top_k: int
    :returns: Hit dicts with ``text``/``source``/``article``/``score`` and
        pinpoint ``locator``/``source_uri``, plus the re-ranker's
        ``retrieval_score``/``rerank_score``/``rerank_position``/``relevant``.
        ``score`` carries the re-ranked value, which unlike a bi-encoder
        similarity is comparable across queries — the comparison
        ``merge_hits`` makes when folding four queries into one list.
    :rtype: list[dict[str, Any]]
    """
    pool = max(top_k, CANDIDATE_POOL)
    try:
        candidates = self._vector_search(query, pool)
    except Exception as exc:  # pragma: no cover
        logger.warning("Qdrant search failed (%s); falling back to built-in KB.", exc)
        candidates = self._builtin_search(query, pool)
    return rerank(query, candidates, top_k)

def lookup(self: "Any", ref: str, top_k: int = 2,
           regulation: str = DEFAULT_REGULATION) -> list[dict[str, Any]]:
    """Fetch the corpus text of the unit *named* ``ref``, by exact match.

    The counterpart to :meth:`search`, for the question search answers
    badly: *what does Article 72 say* is a lookup by identifier, not a
    similarity problem. ``ref`` is an indexed keyword field in the corpus
    payload, so this is a filtered scroll — no embedding, no fusion, no
    re-ranking, and no candidate that merely resembles the article asked
    for. An empty result is therefore meaningful in a way an empty search
    is not: the corpus holds no unit under that reference.

    :param ref: Canonical reference, e.g. ``"Article 72"``, ``"Annex III"``.
    :type ref: str
    :param top_k: Maximum chunks of that unit to return, from its start.
    :type top_k: int
    :param regulation: Payload ``regulation`` to constrain the match to —
        GDPR also has an Article 10, and a bare ref would match both.
    :type regulation: str
    :returns: Hits carrying ``match: "ref_lookup"``, ``score: 1.0`` and
        ``relevant: True``; empty when the corpus holds no such unit.
    :rtype: list[dict[str, Any]]
    """
    if not ref.strip() or top_k <= 0:
        return []
    try:
        return self._qdrant_lookup(ref, top_k, regulation)
    except Exception as exc:  # pragma: no cover
        logger.warning("Qdrant ref lookup for %r failed (%s); falling back to "
                       "built-in KB.", ref, exc)
        return self._kb_lookup(ref, top_k)


__all__ = ["lookup", "search"]
