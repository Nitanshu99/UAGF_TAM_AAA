"""What every ref-lookup hit carries, whichever store answered it."""
from __future__ import annotations

from typing import Any

#: The regulation a bare ``Article N`` citation means in an EU AI Act audit.
#: Required, not optional: GDPR Article 10 is also in this corpus, and an
#: unqualified ``ref == "Article 10"`` filter would return both regulations.
#: The old query string appended "EU AI Act" for exactly this reason — it is
#: the one thing the bare label got right, and the filter keeps it.
DEFAULT_REGULATION = "EU_AI_Act"


def annotate(hit: dict[str, Any], ref: str, position: int) -> dict[str, Any]:
    """Mark *hit* as an identifier match rather than a similarity match.

    ``score`` is 1.0 because an exact match on the cited reference is relevant
    by construction — it *is* the article asked for — and because
    ``merge_hits`` ranks on ``score``, which correctly puts the article itself
    above anything a semantic query guessed at. ``match`` is what tells the
    Verifier which of the two it is holding.

    :param hit: A hit projected from the corpus or the built-in KB.
    :param ref: The reference this lookup asked for.
    :param position: 1-based order within the article, by ``chunk_index``.
    :returns: A new dict; the original is not mutated.
    """
    return {**hit, "score": 1.0, "relevant": True, "match": "ref_lookup",
            "lookup_ref": ref, "rerank_position": position}


__all__ = ["DEFAULT_REGULATION", "annotate"]
