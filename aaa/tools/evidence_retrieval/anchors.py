"""Looking up the anchor references a phase brief names, by identifier."""
from __future__ import annotations

from typing import Any

from aaa.tools.evidence_retrieval.dedup import merge_hits
from aaa.tools.evidence_retrieval.logger import logger
from aaa.tools.evidence_retrieval.refs import cited_references

#: References fetched by identifier per seed. The anchors name at most four
#: (measured), and a query of one kind is already budgeted at
#: ``_MAX_QUERIES_PER_KIND``; a looked-up reference is such a query.
MAX_ANCHOR_REFS = 4
#: Chunks per looked-up reference. Two, for the same reason fix 16 chose two:
#: an article opens with its operative rule, and Article 10's paragraph 5 — the
#: derogation case 01 claims — is the *second* chunk of the two it is split into.
LOOKUP_TOP_K = 2
def _lookup_anchor_refs(rag: Any, query: str, hits: list[Any]) -> list[Any]:
    """Fold in the corpus text of every reference *query* names.

    :param rag: A ``RegulatoryRAG``; a retriever without ``lookup`` is skipped.
    :param query: The authored anchor query, read for the references it names.
    :param hits: Hits retrieved so far; not mutated.
    :returns: The merged list, exact matches ranked above similarity matches.
    """
    lookup = getattr(rag, "lookup", None)
    if lookup is None:
        return hits
    refs = cited_references(query, limit=MAX_ANCHOR_REFS)
    resolved = []
    for ref in refs:
        try:
            found = list(lookup(ref, top_k=LOOKUP_TOP_K))
        except Exception as exc:  # noqa: BLE001 - retrieval must not crash a phase
            logger.warning("Seed ref lookup failed for %s (%s).", ref, exc)
            continue
        if found:
            resolved.append(ref)
            hits, _, _ = merge_hits(hits, found)
    if refs:
        logger.info("Seed: anchor names %d reference(s) %s; resolved by identifier: %s.",
                    len(refs), refs, ", ".join(resolved) or "none")
    return hits


__all__ = ["LOOKUP_TOP_K", "MAX_ANCHOR_REFS", "_lookup_anchor_refs"]
