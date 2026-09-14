"""Pass-A seeding for the phase agents — fix 17.

Each phase agent's first call is seeded by strings fixed at authoring time. The
post-fix run showed those strings are where the model forms its opinion, and
this module widens what they reach — in the direction each corpus actually
rewards, which is not the same direction for both.

**The regulatory anchors are bags of citations.** ``"Article 9 risk management
Article 17 quality management system Article 12 record-keeping logging Article
72 post-market monitoring"`` names four articles and is answered by one query
at ``top_k=3``, so it structurally cannot return them all. Measured live
against the 1,198-point corpus, the five anchors returned **10 of the 13
references they name**: Phase 1 missed **Article 5 and Annex III** and returned
Article 23 — obligations of importers — that nobody asked for, and Phase 5
missed **Article 9**. All three are articles whose artefacts those phases are
accountable for (``T02``→Art. 5, ``T03``→Annex III, ``T14``→Art. 9). This is
finding P1 one level up: *a citation is not a search query*, and fix 16 built
the instrument for it. Every reference an anchor names is now fetched by
identifier through :meth:`RegulatoryRAG.lookup`, and the anchor's own search is
kept for what only it can reach — the Recitals, which no lookup can name.
After the fix, **13 of 13**, with Recitals 67, 70 and 74 still in place.

**Widening is more queries, not longer ones.** The declaration-derived query
(:mod:`~aaa.tools.evidence_retrieval.engagement`) is folded in as its own
retrieval and merged, never concatenated onto the authored string. Both halves
of that were measured; the reasoning and the numbers are in that module, and
the same rule is why the anchor search here is left exactly as its author wrote
it. Nothing in this module edits a query.

Neither seed can exceed what one expansion round could already have produced:
``merge_hits`` caps both kinds at :data:`MAX_HITS_PER_KIND`, and the widened
seeds measured 3–8 regulatory and 4–6 client-document hits against that cap of
12, so the addition displaces nothing.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.client_doc_ingest import client_doc_search
from aaa.tools.evidence_retrieval.anchors import LOOKUP_TOP_K, MAX_ANCHOR_REFS, _lookup_anchor_refs
from aaa.tools.evidence_retrieval.dedup import merge_hits
from aaa.tools.evidence_retrieval.engagement import engagement_query
from aaa.tools.evidence_retrieval.logger import _TOP_K, _no_rag, logger


def seed_regulatory_hits(rag: Any, query: str, top_k: int = _TOP_K) -> list[dict[str, Any]]:
    """Pull the phase's core regulatory passages up front (never raises).

    Two retrievals, merged: the authored *query* as written, and an exact
    lookup of each reference it names. The search supplies the subject matter
    and the Recitals; the lookups guarantee that an anchor naming four articles
    is shown all four rather than whichever three embedded closest.

    :param rag: A ``RegulatoryRAG`` instance, or ``None`` when none is wired.
    :param query: The phase's authored anchor query.
    :param top_k: Passages the anchor search itself returns.
    :returns: De-duplicated, score-ranked hits; ``[]`` when nothing is reachable.
    """
    if not query:
        return []
    if rag is None:
        _no_rag(f"seed query {query!r}")
        return []
    try:
        hits: list[Any] = list(rag.search(query, top_k=top_k))
    except Exception as exc:  # noqa: BLE001 - retrieval must not crash a phase
        logger.warning("Regulatory seed search failed (%s): %s", query, exc)
        hits = []
    searched = len(hits)
    hits = _lookup_anchor_refs(rag, query, hits)
    if not hits:
        logger.warning("Regulatory seed returned no passages for %r.", query)
    elif len(hits) > searched:
        logger.info("Regulatory seed: %d passage(s) from search, %d after "
                    "resolving the references the anchor names.", searched, len(hits))
    return hits


def seed_client_doc_hits(engagement_id: str, query: str, decl: dict[str, Any] | None = None,
                         top_k: int = _TOP_K) -> list[dict[str, Any]]:
    """Search the engagement's dossier on the authored query and on its own terms.

    The authored *query* asks the phase's subject-matter question; the query
    derived from *decl* asks what this particular system is. They are run
    separately and merged, because concatenating them was measured to lose the
    subject-matter hits entirely (see :mod:`.engagement`).

    :param engagement_id: Engagement whose collection is searched ("" disables).
    :param query: The phase's authored client-document query.
    :param decl: The dispatch's ``declaration_summary``; ``None`` skips widening.
    :param top_k: Passages each query returns.
    :returns: De-duplicated, score-ranked hits; ``[]`` when nothing is reachable.
    """
    if not engagement_id or not query:
        return []
    hits: list[Any] = list(client_doc_search(engagement_id, query, top_k=top_k))
    fixed = len(hits)
    derived = engagement_query(decl or {})
    if derived:
        hits, dupes, _ = merge_hits(hits, client_doc_search(engagement_id, derived, top_k=top_k))
        logger.info("Client-doc seed: %d passage(s) on the authored query, %d after "
                    "the declaration-derived query (%d duplicate(s)).",
                    fixed, len(hits), dupes)
    return hits


__all__ = ["LOOKUP_TOP_K", "MAX_ANCHOR_REFS", "seed_client_doc_hits", "seed_regulatory_hits"]
