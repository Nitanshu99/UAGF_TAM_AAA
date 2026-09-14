"""Turning a cross-encoder logit into an annotated hit, and logging what was passed over."""
from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

#: A cross-encoder trained on binary relevance separates at logit 0, so the
#: normalised (sigmoid) boundary is 0.5. Not tuned; inherited from the model.
RELEVANT_ABOVE = 0.5


def _normalise(logit: float) -> float:
    """Map a cross-encoder logit onto ``(0, 1)``.

    Keeps ``score`` on the same scale the bi-encoder produced, so
    ``merge_hits`` (fix 9) ranks a mixed list sanely if re-ranking was
    available for some queries and not others.

    :param logit: Raw cross-encoder output.
    :type logit: float
    :returns: Sigmoid of *logit*; 0.5 is the relevance boundary.
    :rtype: float
    """
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, logit))))


def _annotate(hit: dict[str, Any], logit: float, position: int) -> dict[str, Any]:
    """Return *hit* with its relevance judgement attached; ``text`` untouched.

    ``score`` is overwritten with the normalised cross-encoder value because
    that is what ``merge_hits`` ranks on, and it is the better signal: unlike a
    bi-encoder similarity it is comparable *across queries*, which is exactly
    the comparison merging hits from four different queries makes.

    :param hit: A corpus hit from ``vector_search`` or the built-in KB.
    :type hit: dict[str, Any]
    :param logit: This chunk's raw cross-encoder score for the query.
    :type logit: float
    :param position: 1-based rank after re-ranking.
    :type position: int
    :returns: A new dict; the original is not mutated.
    :rtype: dict[str, Any]
    """
    score = _normalise(logit)
    return {**hit,
            "score": score,
            "retrieval_score": hit.get("score"),
            "rerank_score": logit,
            "rerank_position": position,
            "relevant": score > RELEVANT_ABOVE}


def _label(hit: dict[str, Any]) -> str:
    """Short identifier for a hit in a log line."""
    return str(hit.get("ref") or hit.get("article") or hit.get("locator") or "?")


def _log_outcome(query: str, kept: list[dict[str, Any]],
                 dropped: list[tuple[dict[str, Any], float]]) -> None:
    """Record what was passed over, so the trail shows the whole candidate set.

    :param query: The query re-ranked.
    :type query: str
    :param kept: The hits returned.
    :type kept: list[dict[str, Any]]
    :param dropped: ``(hit, logit)`` pairs that did not make the cut.
    :type dropped: list[tuple[dict[str, Any], float]]
    """
    logger.info(
        "Re-ranked %d candidate(s) for %r → kept %d: %s.",
        len(kept) + len(dropped), query, len(kept),
        ", ".join(f"{_label(h)} {h['score']:.2f}"
                  f"{'' if h['relevant'] else ' (below relevance)'}" for h in kept)
        or "none")
    if dropped:
        logger.info(
            "Not passed for %r: %s. Considered and ranked lower — not absent from "
            "the corpus.", query,
            ", ".join(f"{_label(h)} {_normalise(s):.2f}" for h, s in dropped[:8]))
    if kept and not any(h["relevant"] for h in kept):
        logger.warning(
            "No candidate for %r scored above the relevance boundary; the best was "
            "%.2f. The passages are still returned — treat a conclusion drawn from "
            "them as unevidenced rather than supported.", query, kept[0]["score"])


__all__ = ["RELEVANT_ABOVE", "_annotate", "_label", "_log_outcome", "_normalise"]
