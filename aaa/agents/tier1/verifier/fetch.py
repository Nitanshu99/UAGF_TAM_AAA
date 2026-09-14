"""Fetching the text of a cited reference from the corpus, by identifier then by search."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)



def _fetch(rag: Any, ref: str, top_k: int) -> list[Any]:
    """Fetch one reference: exact lookup first, labelled search only on a miss.

    The order is the whole of fix 16. ``rag.lookup`` matches the corpus payload
    field the citation names, so what comes back *is* Article 72 or nothing;
    ``rag.search`` matches whatever embeds near the string "Article 72 EU AI
    Act", which the post-fix run showed to be Articles 74 and 71. Running the
    search first, or blending the two, would put the second kind of answer in
    front of the Verifier looking exactly like the first.

    :param rag: The ``RegulatoryRAG``.
    :param ref: One canonical reference.
    :param top_k: Passages to pull.
    :returns: Hits for *ref*, possibly empty; never raises.
    """
    lookup = getattr(rag, "lookup", None)
    found: list[Any] = []
    if lookup is None:
        # A retriever that offers no identifier lookup is not a failure to
        # report as one; it simply cannot answer this question exactly.
        logger.info("Retriever offers no ref lookup; %s resolved by search only.", ref)
    else:
        try:
            found = list(lookup(ref, top_k=top_k))
        except Exception as exc:  # noqa: BLE001 - retrieval must not fail a critique
            logger.warning("Verifier citation lookup failed for %s (%s).", ref, exc)
    if found:
        return found
    # The corpus holds no unit under that reference. Subject-matter search is
    # the fallback the fix order asks for, but its results are *about* the
    # citation rather than the citation itself, and they travel labelled as
    # such: a `semantic_fallback` hit must not be read as confirming that the
    # article exists, which is the confusion P1 measured.
    logger.info("Verifier: no corpus unit under %r; falling back to subject-matter "
                "search, whose hits cannot confirm the reference.", ref)
    try:
        neighbours = list(rag.search(f"{ref} EU AI Act", top_k=top_k))
    except Exception as exc:  # noqa: BLE001 - retrieval must not fail a critique
        logger.warning("Verifier citation retrieval failed for %s (%s).", ref, exc)
        return []
    if not neighbours:
        # Not the same as never asking: the corpus was searched and is silent,
        # which is what the prompt's `minor`/unverified route is for.
        logger.info("Verifier citation retrieval returned no passage for %s.", ref)
    return [{**hit, "match": "semantic_fallback", "lookup_ref": ref}
            for hit in neighbours]


__all__ = ["_fetch"]
