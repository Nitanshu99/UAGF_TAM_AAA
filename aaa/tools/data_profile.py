"""
data_profile — Dataset profiling wrapper (§4.1).

Returns a structured summary dict compatible with T07_data_quality_report
``dataset_summary`` block.

Production path:  ydata-profiling (``ProfileReport``).
Offline/fallback: pandas describe()-based stats with no external dependency.

Usage
-----
    from src.tools.data_profile import data_profile

    summary = data_profile(df, target_column="class")
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def data_profile(df: Any, target_column: str | None = None) -> dict[str, Any]:
    """
    Compute a dataset profile summary.

    Parameters
    ----------
    df:
        A ``pandas.DataFrame`` (or duck-typed equivalent).
    target_column:
        Name of the prediction target column; used only for logging.

    Returns
    -------
    dict matching the T07 ``dataset_summary`` sub-schema:
        {
            num_rows, num_columns, data_types_summary,
            duplicate_rows, duplicate_rows_pct,
            memory_usage_bytes, profiling_tool, profiling_tool_version
        }
    """
    try:
        return _profile_ydata(df)
    except Exception as exc:
        logger.info("ydata-profiling unavailable (%s); using pandas fallback.", exc)
        return _profile_pandas(df)


# ---------------------------------------------------------------------------
# ydata-profiling path
# ---------------------------------------------------------------------------

def _profile_ydata(df: Any) -> dict[str, Any]:
    """Use ydata-profiling (formerly pandas-profiling) for a rich profile."""
    from ydata_profiling import ProfileReport  # type: ignore  # pragma: no cover
    import importlib.metadata as meta  # pragma: no cover

    report = ProfileReport(df, minimal=True, progress_bar=False)  # pragma: no cover
    desc = report.get_description()  # pragma: no cover

    overview = desc["overview"]  # pragma: no cover
    num_rows = int(overview["n"])  # pragma: no cover
    num_cols = int(overview["n_var"])  # pragma: no cover
    dup_rows = int(overview.get("n_duplicates", 0))  # pragma: no cover

    # Build dtype summary from variable type counts
    dtypes_summary: dict[str, int] = {}  # pragma: no cover
    for var_info in desc["variables"].values():  # pragma: no cover
        vtype = var_info.get("type", "Unsupported")  # pragma: no cover
        dtypes_summary[vtype] = dtypes_summary.get(vtype, 0) + 1  # pragma: no cover

    try:  # pragma: no cover
        version = meta.version("ydata-profiling")  # pragma: no cover
    except Exception:  # pragma: no cover
        version = "unknown"  # pragma: no cover

    return {  # pragma: no cover
        "num_rows": num_rows,
        "num_columns": num_cols,
        "data_types_summary": dtypes_summary,
        "duplicate_rows": dup_rows,
        "duplicate_rows_pct": round(dup_rows / num_rows * 100, 2) if num_rows else 0.0,
        "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
        "profiling_tool": "ydata-profiling",
        "profiling_tool_version": version,
    }


# ---------------------------------------------------------------------------
# pandas fallback
# ---------------------------------------------------------------------------

def _profile_pandas(df: Any) -> dict[str, Any]:
    """Pure-pandas fallback — no extra dependencies required."""
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        # Absolutely no pandas → return a minimal stub
        return {
            "num_rows": 0,
            "num_columns": 0,
            "data_types_summary": {},
            "duplicate_rows": None,
            "duplicate_rows_pct": None,
            "memory_usage_bytes": None,
            "profiling_tool": "offline-stub",
            "profiling_tool_version": None,
        }

    num_rows, num_cols = df.shape

    # Summarise dtype categories
    dtypes_summary: dict[str, int] = {}
    for dtype in df.dtypes:
        if hasattr(dtype, "name"):
            if "int" in dtype.name or "float" in dtype.name:
                key = "Numeric"
            elif "object" in dtype.name or "string" in dtype.name:
                key = "Categorical"
            elif "bool" in dtype.name:
                key = "Boolean"
            elif "datetime" in dtype.name:
                key = "DateTime"
            else:
                key = "Other"
            dtypes_summary[key] = dtypes_summary.get(key, 0) + 1

    try:
        dup_rows = int(df.duplicated().sum())
        dup_pct = round(dup_rows / num_rows * 100, 2) if num_rows else 0.0
        mem_bytes = int(df.memory_usage(deep=True).sum())
    except Exception:
        dup_rows, dup_pct, mem_bytes = None, None, None

    try:
        import importlib.metadata as meta
        pd_version = meta.version("pandas")
    except Exception:
        pd_version = getattr(pd, "__version__", "unknown")

    return {
        "num_rows": num_rows,
        "num_columns": num_cols,
        "data_types_summary": dtypes_summary,
        "duplicate_rows": dup_rows,
        "duplicate_rows_pct": dup_pct,
        "memory_usage_bytes": mem_bytes,
        "profiling_tool": "pandas",
        "profiling_tool_version": pd_version,
    }
