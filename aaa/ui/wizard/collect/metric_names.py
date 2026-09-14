"""The metric names that mark a component discriminative, and the generative modalities."""
from __future__ import annotations

import re

#: Metric families only a ranking or classification model reports.
_DISCRIMINATIVE_METRIC = re.compile(
    r"^(precision|recall|ndcg|map|mrr|hit_rate|auc|roc_auc|pr_auc|f1|fbeta|"
    r"accuracy|balanced_accuracy|log_loss|brier)(_at_\d+|@\d+)?$|_at_\d+$|@\d+$",
    re.IGNORECASE)
#: Generative modalities: only these can carry a *second*, discriminative part.
_GENERATIVE = frozenset({"llm", "agentic", "gpai"})


__all__ = ["_DISCRIMINATIVE_METRIC", "_GENERATIVE"]
