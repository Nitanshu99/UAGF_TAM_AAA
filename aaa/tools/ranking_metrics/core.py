"""Ranking metrics recomputed from the ranked outputs an evaluation set records.

A ranking system declares precision@k and
NDCG@k, and those can be reproduced without the model when the evaluation set holds
each query's ranked rows and a relevance label. The columns are declared in the data
dictionary (``ranking.query_column``, ``ranking.rank_column``), never inferred. The
interval resamples queries, not rows: rows within one query are not independent.
"""
from __future__ import annotations

import re
from typing import Any, Sequence

from aaa.tools.metric_suite.interval import LEVEL, ROUNDS, SEED
from aaa.tools.ranking_metrics.per_query import ndcg_at, precision_at

#: Declared metric names this tool recomputes: ``precision_at_5``, ``ndcg_at_10``.
NAME = re.compile(r"(precision|ndcg)_at_(\d+)")
_FUNCTIONS = {"precision": precision_at, "ndcg": ndcg_at}


def per_query_values(frame: Any, query: str, rank: str, relevant: Sequence[bool],
                     name: str) -> list[float]:
    """The metric *name* for every query where it is defined.

    :param frame: The evaluation set.
    :param query: Column identifying the query.
    :param rank: Column holding the system's rank (1 = first).
    :param relevant: Row-aligned relevance.
    :param name: A :data:`NAME` metric.
    """
    family, k = NAME.fullmatch(name).groups()  # type: ignore[union-attr]
    ranked = frame.assign(_relevant=list(relevant)).sort_values([query, rank], kind="stable")
    values = (_FUNCTIONS[family](group["_relevant"].tolist(), int(k))
              for _, group in ranked.groupby(query, sort=True))
    return [v for v in values if v is not None]


def query_bootstrap(values: Sequence[float]) -> tuple[float, float] | None:
    """Percentile interval of the mean over resampled queries (seeded)."""
    import numpy as np  # type: ignore

    if len(values) < 2:
        return None
    data = np.asarray(values, dtype=float)
    means = data[np.random.default_rng(SEED).integers(0, len(data), (ROUNDS, len(data)))].mean(1)
    tail = (1 - LEVEL) / 2 * 100
    return float(np.percentile(means, tail)), float(np.percentile(means, 100 - tail))


def ranking_metrics(frame: Any, ranking: dict[str, Any], target: str | None,
                    positive_label: Any, names: Sequence[str]) -> dict[str, Any]:
    """Recompute the declared ranking metrics *names* with query-level intervals.

    :param frame: The evaluation set.
    :param ranking: Declared ``{query_column, rank_column}``.
    :param target: Declared relevance column (the data dictionary's target).
    :param positive_label: Its relevant value.
    :param names: Declared metric names matching :data:`NAME`.
    :returns: ``{computed, reason, n_queries, n_rows, metrics, intervals, method}``.
    """
    query, rank = ranking.get("query_column"), ranking.get("rank_column")
    missing = [c for c in (query, rank, target) if not c or c not in getattr(frame, "columns", [])]
    base: dict[str, Any] = {"metrics": {}, "intervals": {}, "n_queries": None, "n_rows": None,
                            "method": ("per-query precision@k / binary-gain NDCG@k over the rows "
                                       "ranked by rank_column, averaged over queries; 95% "
                                       f"percentile bootstrap over queries ({ROUNDS} resamples)")}
    if missing or not names:
        return {**base, "computed": False,
                "reason": f"ranking columns not in the evaluation set: {missing}" if missing
                else "no ranking metric was declared"}
    relevant = [str(v) == str(positive_label) for v in frame[target].tolist()]
    values = {n: per_query_values(frame, str(query), str(rank), relevant, n) for n in names}
    return {**base, "computed": True, "reason": None, "n_rows": len(frame),
            "n_queries": int(frame[query].nunique()),
            "metrics": {n: sum(v) / len(v) for n, v in values.items() if v},
            "intervals": {n: iv for n, v in values.items() if (iv := query_bootstrap(v))}}


__all__ = ["NAME", "per_query_values", "query_bootstrap", "ranking_metrics"]
