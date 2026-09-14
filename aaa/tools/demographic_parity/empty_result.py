"""Part 4 of the former ``demographic_parity`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.demographic_parity.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.demographic_parity.compute.python import _compute_python  # noqa: F401
from aaa.tools.demographic_parity.logger import logger  # noqa: F401


def _empty_result(positive_label: Any) -> dict[str, Any]:
    """Return an empty demographic-parity result stub."""
    return {
        "metric": "demographic_parity",
        "difference": None,
        "ratio": None,
        "group_rates": [],
        "verdict": "NOT_TESTED",
        # Not computed: no sample, rather than a sample of zero (T-20260913-033).
        "sample_size": None,
        "tool": None,
        "positive_label": str(positive_label),
    }


def demographic_parity(
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute demographic-parity difference and ratio.

    Parameters
    ----------
    y_pred:
        Predicted labels.  Empty / None → returns an empty-result stub.
    sensitive_features:
        Group label per prediction (e.g. ``"M"``/``"F"``).  Must be the
        same length as ``y_pred``.
    positive_label:
        Value treated as the positive outcome when computing selection rate.

    Returns
    -------
    dict matching the T12 ``demographic_parity`` sub-schema:
        {
            metric, difference, ratio, group_rates,
            verdict, sample_size, tool, positive_label
        }
    """
    if (y_pred is None or sensitive_features is None
            or len(y_pred) == 0 or len(sensitive_features) == 0
            or len(y_pred) != len(sensitive_features)):
        return _empty_result(positive_label)

    try:
        return _compute_fairlearn(y_pred, sensitive_features, positive_label)
    except Exception as exc:
        logger.info("fairlearn unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_pred, sensitive_features, positive_label)
