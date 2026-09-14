"""Part 4 of the former ``disparate_impact`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.disparate_impact.compute.aif360 import _compute_aif360  # noqa: F401
from aaa.tools.disparate_impact.empty_result import _empty_result  # noqa: F401
from aaa.tools.disparate_impact.groups import comparison_pair, group_counts, selection_rates
from aaa.tools.disparate_impact.logger import _assemble_result, logger  # noqa: F401


def _compute_python(
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    privileged_group: Any | None,
    positive_label: Any,
) -> dict[str, Any]:
    """Pure-Python selection-rate ratio (four-fifths rule)."""
    counts = group_counts(y_pred, sensitive_features, positive_label)
    if not counts:
        return _empty_result(privileged_group, positive_label)

    rates = selection_rates(counts)
    # The least-selected group against the most-selected one, not whichever two
    # the row order or the alphabet offered first.
    priv, unpriv = comparison_pair(rates, privileged_group)
    priv_rate, unpriv_rate = rates[priv], rates[unpriv]
    ratio = (unpriv_rate / priv_rate) if priv_rate else None  # nobody selected: no ratio

    return _assemble_result(
        ratio, priv, unpriv, priv_rate, unpriv_rate,
        len(y_pred), "pure-python", positive_label,
        counts=(counts[priv], counts[unpriv]),
    )
