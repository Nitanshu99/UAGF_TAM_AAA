"""metric_suite — Performance-metric computation wrapper (§4.2).

Returns a structured dict compatible with the T09_model_card
``performance_metrics`` block.

Production path:  scikit-learn metrics + (optional) torchmetrics.
Fallback: pure-Python accuracy / F1 / AUC implementations.

Usage
-----
    from src.tools.metric_suite import metric_suite

    metrics = metric_suite(y_true, y_pred, y_proba=None, task="classification")"""
from aaa.tools.metric_suite.compute.python import _compute_python, _empty_result  # noqa: F401
from aaa.tools.metric_suite.compute.sklearn import _compute_sklearn  # noqa: F401
from aaa.tools.metric_suite.core import metric_suite  # noqa: F401
from aaa.tools.metric_suite.logger import (  # noqa: F401
    _DEFAULT_PRIMARY,
    _sklearn_classification,
    logger,
)
from aaa.tools.metric_suite.macro_f1 import _macro_f1  # noqa: F401

__all__ = [
    'logger', '_DEFAULT_PRIMARY', '_sklearn_classification', '_compute_sklearn', '_macro_f1',
    '_compute_python', '_empty_result', 'metric_suite',
]
