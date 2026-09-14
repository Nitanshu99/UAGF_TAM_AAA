"""Part 1 of the former ``data_profile`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _profile_ydata(df: Any) -> dict[str, Any]:
    """Use ydata-profiling (formerly pandas-profiling) for a rich profile."""
    import importlib.metadata as meta  # pragma: no cover

    from ydata_profiling import ProfileReport  # type: ignore  # pragma: no cover

    report = ProfileReport(df, minimal=True, progress_bar=False)  # pragma: no cover
    # BaseDescription is a dataclass in the stubs but subscriptable at runtime.
    desc: Any = report.get_description()  # pragma: no cover

    overview = desc["overview"]  # pragma: no cover
    num_rows = int(overview["n"])  # pragma: no cover
    num_cols = int(overview["n_var"])  # pragma: no cover
    dup_rows = overview.get("n_duplicates")  # pragma: no cover

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
        "duplicate_rows": None if dup_rows is None else int(dup_rows),
        "duplicate_rows_pct": (round(int(dup_rows) / num_rows * 100, 2)
                               if num_rows and dup_rows is not None else None),
        "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
        "profiling_tool": "ydata-profiling",
        "profiling_tool_version": version,
    }
