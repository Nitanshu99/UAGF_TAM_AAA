"""fairness_groups — which cohorts a group-fairness metric may be computed over.

Bins a continuous protected attribute into quantile bands, and declines only a
grouping with fewer than two cohorts.  See :mod:`aaa.tools.fairness_groups.resolve`
(findings Q2 and Q3) and :mod:`aaa.tools.fairness_ci.decision` for how small
cohorts are handled.

Usage
-----
    from aaa.tools.fairness_groups import resolve_groups

    resolution = resolve_groups("age", [18, 19, 20, ...])
    if resolution.tested:
        demographic_parity(y_pred=y_pred, sensitive_features=resolution.labels)
"""
from aaa.tools.fairness_groups.binning import as_floats, bin_values, is_continuous  # noqa: F401
from aaa.tools.fairness_groups.logger import MAX_DISCRETE_LEVELS, TARGET_BINS, logger  # noqa: F401
from aaa.tools.fairness_groups.resolve import GroupResolution, resolve_groups  # noqa: F401

__all__ = [
    'logger',
    'MAX_DISCRETE_LEVELS',
    'TARGET_BINS',
    'as_floats',
    'is_continuous',
    'bin_values',
    'GroupResolution',
    'resolve_groups',
]
