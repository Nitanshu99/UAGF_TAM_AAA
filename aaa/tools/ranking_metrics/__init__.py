"""ranking_metrics — declared precision@k / NDCG@k recomputed from supplied ranked outputs.

Usage
-----
    from aaa.tools.ranking_metrics import ranking_metrics

    result = ranking_metrics(frame, {"query_column": "query_id", "rank_column": "rank"},
                             "relevant", 1, ["precision_at_5", "ndcg_at_10"])
"""
from aaa.tools.ranking_metrics.core import NAME, per_query_values, query_bootstrap, ranking_metrics
from aaa.tools.ranking_metrics.per_query import ndcg_at, precision_at

__all__ = ["NAME", "ndcg_at", "per_query_values", "precision_at", "query_bootstrap",
           "ranking_metrics"]
