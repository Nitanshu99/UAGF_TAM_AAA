"""Part 5 of the former ``disparate_impact`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.disparate_impact.compute.aif360 import _compute_aif360  # noqa: F401
from aaa.tools.disparate_impact.compute.python import _compute_python  # noqa: F401
from aaa.tools.disparate_impact.empty_result import _empty_result  # noqa: F401
from aaa.tools.disparate_impact.logger import _assemble_result, logger  # noqa: F401


def disparate_impact(
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    privileged_group: Any | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute disparate-impact ratio (unprivileged_selection / privileged_selection).

    Parameters
    ----------
    y_pred:
        Predicted labels.
    sensitive_features:
        Group label per prediction.
    privileged_group:
        Label of the privileged group.  If ``None`` the most-selected group
        is treated as privileged (heuristic).
    positive_label:
        Value treated as the positive outcome.

    Returns
    -------
    dict matching the T12 ``disparate_impact`` sub-schema:
        {
            metric, ratio, privileged_group, unprivileged_group,
            privileged_selection_rate, unprivileged_selection_rate,
            four_fifths_rule_passed, verdict,
            sample_size, tool, positive_label
        }
    """
    if (y_pred is None or sensitive_features is None
            or len(y_pred) == 0 or len(sensitive_features) == 0
            or len(y_pred) != len(sensitive_features)):
        return _empty_result(privileged_group, positive_label)

    try:
        return _compute_aif360(y_pred, sensitive_features, privileged_group, positive_label)
    except Exception as exc:
        logger.info("aif360 unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_pred, sensitive_features, privileged_group, positive_label)
