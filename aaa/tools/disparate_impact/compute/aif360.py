"""Part 2 of the former ``disparate_impact`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.disparate_impact.groups import comparison_pair, group_counts, selection_rates
from aaa.tools.disparate_impact.logger import _assemble_result, logger  # noqa: F401


def _compute_aif360(
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    privileged_group: Any | None,
    positive_label: Any,
) -> dict[str, Any]:
    """Use IBM AIF360 BinaryLabelDatasetMetric for disparate-impact."""
    import pandas as pd  # type: ignore
    from aif360.datasets import BinaryLabelDataset  # type: ignore
    from aif360.metrics import BinaryLabelDatasetMetric  # type: ignore

    counts = group_counts(y_pred, sensitive_features, positive_label)
    # The least-selected group against the most-selected one. Sorting the labels
    # and taking the first two compared whichever cohorts the alphabet offered.
    priv, unpriv = comparison_pair(selection_rates(counts), privileged_group)

    # Restricted to the two groups the result names. aif360 binarises to
    # privileged-vs-everything-else, so on three or more groups the ratio it
    # returned was against a pooled remainder while the artefact reported a
    # single unprivileged label — a number that did not describe the comparison
    # it was printed beside.
    pairs = [(p, str(g)) for p, g in zip(y_pred, sensitive_features)
             if str(g) in (priv, unpriv)]
    df = pd.DataFrame({
        "label": [1 if p == positive_label else 0 for p, _ in pairs],
        "group": [1 if g == priv else 0 for _, g in pairs],
    })
    bld = BinaryLabelDataset(
        df=df, label_names=["label"], protected_attribute_names=["group"],
        favorable_label=1, unfavorable_label=0,
    )
    metric = BinaryLabelDatasetMetric(
        bld,
        unprivileged_groups=[{"group": 0}],
        privileged_groups=[{"group": 1}],
    )
    # ``base_rate`` is AIF360's name for the selection rate (share of favorable
    # outcomes in the group). ``BinaryLabelDatasetMetric`` has never exposed a
    # ``selection_rate``; calling it raised AttributeError on every input, so
    # this branch always fell through to the pure-Python path.
    ratio = float(metric.disparate_impact())
    priv_rate = float(metric.base_rate(privileged=True))
    unpriv_rate = float(metric.base_rate(privileged=False))
    return _assemble_result(
        ratio, priv, unpriv, priv_rate, unpriv_rate,
        len(y_pred), "aif360", positive_label,
        counts=(counts.get(priv, (0, 0)), counts.get(unpriv, (0, 0))),
    )
