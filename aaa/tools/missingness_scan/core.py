"""Part 2 of the former ``missingness_scan`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.missingness_scan.logger import (  # noqa: F401
    _DEFAULT_THRESHOLD,
    _empty_result,
    logger,
)


def missingness_scan(
    df: Any,
    high_missingness_threshold: float = _DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """
    Compute per-column missingness rates.

    Parameters
    ----------
    df:
        A ``pandas.DataFrame``.
    high_missingness_threshold:
        Percentage (0–100) above which a column is flagged as
        high-missingness (default 20 %).

    Returns
    -------
    dict matching the T07 ``missingness`` sub-schema:
        {
            columns: [{column_name, missing_count, missing_pct}],
            overall_missingness_pct,
            high_missingness_columns,
            threshold_used
        }
    """
    import importlib.util
    if importlib.util.find_spec("pandas") is None:
        logger.warning("pandas not installed; returning empty missingness stub.")
        return _empty_result(high_missingness_threshold)

    num_rows, _ = df.shape
    if num_rows == 0:
        return _empty_result(high_missingness_threshold)

    columns_result: list[dict[str, Any]] = []
    high_miss: list[str] = []
    total_missing = 0

    for col in df.columns:
        try:
            missing_count = int(df[col].isna().sum())
        except Exception:
            missing_count = 0

        missing_pct = round(missing_count / num_rows * 100, 4) if num_rows else 0.0
        columns_result.append(
            {
                "column_name": str(col),
                "missing_count": missing_count,
                "missing_pct": missing_pct,
            }
        )
        total_missing += missing_count
        if missing_pct > high_missingness_threshold:
            high_miss.append(str(col))

    total_cells = num_rows * len(df.columns) if len(df.columns) > 0 else 1
    overall_pct = round(total_missing / total_cells * 100, 4) if total_cells else 0.0

    return {
        "columns": columns_result,
        "overall_missingness_pct": overall_pct,
        "high_missingness_columns": high_miss,
        "threshold_used": high_missingness_threshold,
    }
