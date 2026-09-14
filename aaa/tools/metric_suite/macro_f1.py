"""Part 3 of the former ``metric_suite`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.metric_suite.compute.sklearn import _compute_sklearn  # noqa: F401
from aaa.tools.metric_suite.logger import (  # noqa: F401
    _DEFAULT_PRIMARY,
    _sklearn_classification,
    logger,
)


def _macro_f1(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
    """Compute macro-averaged F1 with no external dependencies."""
    labels = sorted({*y_true, *y_pred})
    if not labels:
        return 0.0
    f1s: list[float] = []
    for lab in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == lab and b == lab)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != lab and b == lab)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == lab and b != lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0
