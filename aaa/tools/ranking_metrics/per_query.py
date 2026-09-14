"""Precision@k and NDCG@k for one query's ranked rows."""
from __future__ import annotations

import math
from typing import Sequence


def precision_at(relevant: Sequence[bool], k: int) -> float | None:
    """Share of relevant items among the first *k* ranked (fewer when the list is shorter).

    A query that records fewer than *k* ranked items is judged on the items it has:
    dividing by *k* would count candidates the system never returned as misses.

    :param relevant: Relevance of each ranked item, best rank first.
    :param k: Cut-off.
    :returns: The precision, or ``None`` for an empty list.
    """
    top = list(relevant[:k])
    return sum(top) / len(top) if top else None


def ndcg_at(relevant: Sequence[bool], k: int) -> float | None:
    """Normalised discounted cumulative gain at *k* with binary gain (Järvelin & Kekäläinen, 2002).

    :param relevant: Relevance of each ranked item, best rank first.
    :param k: Cut-off.
    :returns: NDCG, or ``None`` when the query holds no relevant item (the ideal gain is 0).
    """
    gains = [float(r) for r in relevant]
    ideal = _dcg(sorted(gains, reverse=True)[:k])
    return _dcg(gains[:k]) / ideal if ideal else None


def _dcg(gains: Sequence[float]) -> float:
    """Discounted cumulative gain, log2(position + 1) discount from position 1."""
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


__all__ = ["ndcg_at", "precision_at"]
