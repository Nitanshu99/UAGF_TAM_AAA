"""Population Stability Index between a reference and a current distribution.

PSI is the standard drift statistic the mock cases' own monitoring plans name
("alert at PSI > 0.2"), so the auditor computes the same measure the provider
claims to monitor. Conventional bands: < 0.1 stable, 0.1–0.2 moderate shift,
> 0.2 significant shift.
"""
from __future__ import annotations

from typing import Any, Sequence

STABLE, MODERATE = 0.1, 0.2

#: floor applied to empty bins so the log ratio stays finite.
_EPS = 1e-4


def _numeric_psi(ref: list[float], cur: list[float], bins: int) -> float:
    """PSI over quantile bins of a numeric feature.

    :param ref: Reference (training) values.
    :type ref: list[float]
    :param cur: Current (evaluation) values.
    :type cur: list[float]
    :param bins: Number of quantile bins.
    :type bins: int
    :returns: The PSI value.
    :rtype: float
    """
    import numpy as np  # type: ignore

    edges = np.unique(np.quantile(ref, [i / bins for i in range(bins + 1)]))
    if len(edges) < 3:
        # A near-constant reference has no quantile bins. It used to score 0.0
        # ("stable") whatever the current data held; its few values are compared
        # as categories instead, so a shift away from the constant still shows.
        return _categorical_psi(ref, cur)
    ref_pct = np.histogram(ref, bins=edges)[0] / len(ref)
    cur_pct = np.histogram(cur, bins=edges)[0] / len(cur)
    ref_pct = np.clip(ref_pct, _EPS, None)
    cur_pct = np.clip(cur_pct, _EPS, None)
    return float(((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)).sum())


def _categorical_psi(ref: Sequence[Any], cur: Sequence[Any]) -> float:
    """PSI over the observed categories of a discrete feature.

    :param ref: Reference (training) values.
    :type ref: Sequence[Any]
    :param cur: Current (evaluation) values.
    :type cur: Sequence[Any]
    :returns: The PSI value.
    :rtype: float
    """
    import math

    categories = set(map(str, ref)) | set(map(str, cur))
    total = 0.0
    for cat in categories:
        r = max(sum(1 for v in ref if str(v) == cat) / max(len(ref), 1), _EPS)
        c = max(sum(1 for v in cur if str(v) == cat) / max(len(cur), 1), _EPS)
        total += (c - r) * math.log(c / r)
    return float(total)


def band(psi: float) -> str:
    """Return the conventional stability band for *psi*.

    :param psi: A PSI value.
    :type psi: float
    :returns: ``"stable"``, ``"moderate_shift"`` or ``"significant_shift"``.
    :rtype: str
    """
    if psi < STABLE:
        return "stable"
    return "moderate_shift" if psi < MODERATE else "significant_shift"
