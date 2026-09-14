"""Part 3 of the former ``data_profile`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.data_profile.dtype_summary import _dtype_summary  # noqa: F401
from aaa.tools.data_profile.logger import _profile_ydata, logger  # noqa: F401
from aaa.tools.data_profile.unmeasured import not_profiled


def _profile_pandas(df: Any) -> dict[str, Any]:
    """Pure-pandas fallback — no extra dependencies required."""
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return not_profiled()

    num_rows, num_cols = df.shape
    dtypes_summary = _dtype_summary(df)

    try:
        dup_rows = int(df.duplicated().sum())
        dup_pct = round(dup_rows / num_rows * 100, 2) if num_rows else None
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
