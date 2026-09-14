"""Part 3 of the former ``shap_explain`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.shap_explain.is_numeric import _is_numeric  # noqa: F401
from aaa.tools.shap_explain.logger import (  # noqa: F401
    _DEFAULT_SAMPLE,
    _DEFAULT_TOP_K,
    _columns_of,
    _explain_shap,
    _row_count,
    logger,
)


def _infer_feature_names(X: Any) -> list[str]:
    cols = _columns_of(X)
    if cols:
        return cols
    try:
        ncol = X.shape[1]
        return [f"f{i}" for i in range(ncol)]
    except Exception:
        return []


def _empty_result(reason: str | None = None) -> dict[str, Any]:
    """Nothing explained: no importances, and — when a model was supplied — why.

    :param reason: Why SHAP could not run on a supplied model; carried as
        ``degraded_reason`` for the caller, stripped before T10 is written.
    """
    result: dict[str, Any] = {
        "technique": "none",
        "feature_importance": [],
        "sample_size": None,  # nothing was explained (T-20260913-039)
        "tool": None,
    }
    if reason:
        result["degraded_reason"] = reason
    return result


def shap_explain(
    model: Any = None,
    X: Any = None,
    feature_names: Sequence[str] | None = None,
    sample_size: int = _DEFAULT_SAMPLE,
    top_k: int = _DEFAULT_TOP_K,
) -> dict[str, Any]:
    """
    Compute global feature importance via SHAP, or report that none was computed.

    Parameters
    ----------
    model:
        Trained model with ``predict`` / ``predict_proba``.  Without one
        nothing is attributed: column variances describe the data, not the
        model, and were once reported here as its importances (T-20260913-061).
    X:
        Tabular feature matrix (``pandas.DataFrame`` or 2-D array).
    feature_names:
        Column names; inferred from ``X.columns`` if available.
    sample_size:
        Maximum rows to feed into SHAP (capped for runtime).
    top_k:
        Return at most this many features in ``feature_importance``.

    Returns
    -------
    dict matching the T10 ``global_explanation`` sub-schema.
    """
    if X is None:
        return _empty_result()

    names = list(feature_names) if feature_names else _infer_feature_names(X)
    n_rows = _row_count(X)
    if n_rows == 0 or not names:
        return _empty_result()

    if model is None:
        return _empty_result()
    try:
        return _explain_shap(model, X, names, sample_size, top_k)
    except Exception as exc:
        logger.info("SHAP unavailable (%s); no importances reported.", exc)
        return _empty_result(f"SHAP could not run on the supplied matrix: {exc}")
