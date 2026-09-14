"""Which two groups the four-fifths ratio compares, and why it must not be luck.

Both compute paths chose the comparison pair by **name**, not by outcome.  The
aif360 path — the one that actually runs — took ``priv = sorted(groups)[0]`` and
``unpriv`` the next label alphabetically; the pure-Python fallback took the
highest-rate group as privileged and then whichever other group happened to come
first in row order.  Two consequences, both visible in the case 01 run:

*The pair was arbitrary.*  ``age`` reported ``0.933`` for ``'18'`` against
``'19'`` — two cohorts of six and three rows, picked because "18" sorts before
"19".  That is the ``PASS`` which contradicted the same artefact's own
demographic-parity ``FAIL``, and it would have moved had the ages been labelled
differently.

*The label misdescribed the computation.*  aif360 binarises to *privileged* vs
*everything else*, so the ratio was ``rate(all groups but '18') / rate('18')``
while the artefact recorded ``unprivileged_group: '19'``.  On ``foreign_worker``
the alphabetical pick made the 10-row ``'no'`` cohort the privileged reference —
the right direction, by accident of spelling.

The EEOC's four-fifths rule compares the **least-selected** group with the
**most-selected** one.  That is what is chosen here, deterministically and by
rate, and both paths then compute the ratio between exactly the two groups the
artefact names.  A declared ``privileged_group`` still wins — the client's own
declaration is evidence about which group is advantaged — and only the
unprivileged side is then derived.
"""
from __future__ import annotations

from typing import Any, Sequence


def group_counts(y_pred: Sequence[Any], sensitive_features: Sequence[Any],
                 positive_label: Any) -> dict[str, tuple[int, int]]:
    """Count ``(selected, total)`` per group.

    :param y_pred: Predicted labels.
    :param sensitive_features: Group label per prediction.
    :param positive_label: Value treated as the favourable outcome.
    :returns: ``{group: (selected, total)}``.
    """
    counts: dict[str, tuple[int, int]] = {}
    for pred, group in zip(y_pred, sensitive_features):
        key = str(group)
        selected, total = counts.get(key, (0, 0))
        counts[key] = (selected + (1 if pred == positive_label else 0), total + 1)
    return counts


def selection_rates(counts: dict[str, tuple[int, int]]) -> dict[str, float]:
    """Selection rate per group from ``(selected, total)`` counts."""
    return {group: (selected / total if total else 0.0)
            for group, (selected, total) in counts.items()}


def comparison_pair(rates: dict[str, float],
                    privileged_group: Any | None) -> tuple[str, str]:
    """Choose ``(privileged, unprivileged)`` — most-selected against least-selected.

    Ties break on the group name so the pair is reproducible: a client re-running
    the audit on the same data must get the same two cohorts named.

    :param rates: Selection rate per group.
    :param privileged_group: The client's declared privileged group, if any.
    :returns: ``(privileged, unprivileged)``; equal when only one group exists.
    """
    if not rates:
        return "", ""
    declared = str(privileged_group) if privileged_group is not None else None
    priv = declared if declared in rates else max(rates, key=lambda g: (rates[g], g))
    others = {g: r for g, r in rates.items() if g != priv}
    if not others:
        return priv, priv
    return priv, min(others, key=lambda g: (others[g], g))


__all__ = ["group_counts", "selection_rates", "comparison_pair"]
