"""Per-feature drift between the training and evaluation datasets (Art. 10).

Answers the question Annex IV §2 / Art. 10 §2(g) put to a provider: does the
data the model is evaluated on still resemble the data it was trained on? A
significant shift undermines every downstream performance and fairness claim,
so the result feeds Phase 2's data-quality verdict.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.drift_test.psi import MODERATE, _categorical_psi, _numeric_psi, band

logger = logging.getLogger(__name__)

_DEFAULT_BINS = 10

#: A discrete column whose values are nearly all distinct (identifiers, free
#: text) shares almost no categories between two samples, so categorical PSI
#: saturates and reports drift for every such column. Those columns carry no
#: distributional signal at this granularity and are skipped.
_MAX_UNIQUE_RATIO = 0.5
_MAX_CATEGORIES = 50


def _is_high_cardinality(values: Any) -> bool:
    """True when a discrete column is an identifier or free-text field.

    :param values: The column's non-null values.
    :type values: Any
    :returns: Whether categorical PSI would be meaningless for it.
    :rtype: bool
    """
    n_unique = values.nunique()
    return n_unique > _MAX_CATEGORIES or n_unique / max(len(values), 1) > _MAX_UNIQUE_RATIO


def _empty(reason: str) -> dict[str, Any]:
    """Build the not-computed result.

    :param reason: Why drift could not be measured.
    :type reason: str
    :returns: Result dict with ``computed`` false.
    :rtype: dict[str, Any]
    """
    return {"computed": False, "reason": reason, "features": [],
            "max_psi": None, "drifted_features": [], "verdict": "NOT_COMPUTED"}


def drift_test(reference: Any = None, current: Any = None,
               bins: int = _DEFAULT_BINS) -> dict[str, Any]:
    """Compute per-feature PSI between *reference* and *current* frames.

    :param reference: Training dataframe (the reference distribution).
    :type reference: Any
    :param current: Evaluation dataframe (the current distribution).
    :type current: Any
    :param bins: Quantile bins for numeric features.
    :type bins: int
    :returns: ``{computed, features[{feature, psi, band, kind}], max_psi,
        drifted_features, verdict}``; fail-soft with ``computed`` false when
        either frame is missing or shares no columns.
    :rtype: dict[str, Any]
    """
    if reference is None or current is None:
        return _empty("training or evaluation dataset unavailable")
    try:
        import pandas as pd  # type: ignore

        shared = [c for c in reference.columns if c in current.columns]
        if not shared:
            return _empty("no overlapping columns between the two datasets")
        features: list[dict[str, Any]] = []
        for col in shared:
            ref_col, cur_col = reference[col].dropna(), current[col].dropna()
            if ref_col.empty or cur_col.empty:
                continue
            numeric = pd.api.types.is_numeric_dtype(ref_col)
            if not numeric and _is_high_cardinality(ref_col):
                features.append({"feature": str(col), "psi": None, "band": "not_comparable",
                                 "kind": "high_cardinality"})
                continue
            psi = (_numeric_psi(list(map(float, ref_col)), list(map(float, cur_col)), bins)
                   if numeric else _categorical_psi(list(ref_col), list(cur_col)))
            features.append({"feature": str(col), "psi": round(psi, 4),
                             "band": band(psi), "kind": "numeric" if numeric else "categorical"})
        scored = [f for f in features if f["psi"] is not None]
        if not scored:
            return _empty("no comparable non-empty columns")
        drifted = [f["feature"] for f in scored if f["psi"] >= MODERATE]
        max_psi = max(f["psi"] for f in scored)
        return {"computed": True, "reason": None, "features": features,
                "max_psi": max_psi, "drifted_features": drifted,
                "verdict": "FAIL" if drifted else "PASS"}
    except Exception as exc:  # noqa: BLE001 — drift must never break Phase 2
        logger.info("drift_test unavailable (%s); returning not-computed.", exc)
        return _empty(f"drift computation failed: {exc}")
