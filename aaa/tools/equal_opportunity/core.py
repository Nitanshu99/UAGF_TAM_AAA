"""Part 4 of the former ``equal_opportunity`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.equal_opportunity.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.equal_opportunity.compute.python import _compute_python, _empty_result  # noqa: F401
from aaa.tools.equal_opportunity.logger import logger  # noqa: F401


def equal_opportunity(
    y_true: Sequence[Any] | None = None,
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute equal-opportunity difference (max TPR gap across groups).

    Parameters
    ----------
    y_true, y_pred:
        Ground-truth + predicted labels.  Must be equal length.
    sensitive_features:
        Group label per prediction.  Must match y_pred length.
    positive_label:
        Value treated as the positive outcome.

    Returns
    -------
    dict matching the T12 ``equal_opportunity`` sub-schema:
        {
            metric, difference, tpr_by_group, verdict,
            sample_size, tool, positive_label
        }
    """
    if (y_true is None or y_pred is None or sensitive_features is None
            or len(y_true) == 0 or len(y_pred) == 0
            or len(y_true) != len(y_pred)
            or len(y_pred) != len(sensitive_features)):
        return _empty_result(positive_label)

    try:
        return _compute_fairlearn(y_true, y_pred, sensitive_features, positive_label)
    except Exception as exc:
        logger.info("fairlearn unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_true, y_pred, sensitive_features, positive_label)
