"""Part 4 of the former ``data_profile`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.data_profile.dtype_summary import _dtype_summary  # noqa: F401
from aaa.tools.data_profile.logger import _profile_ydata, logger  # noqa: F401
from aaa.tools.data_profile.profile_pandas import _profile_pandas  # noqa: F401
from aaa.tools.data_profile.unmeasured import not_profiled


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
    if df is None or len(df) == 0:
        return not_profiled()  # no rows: nothing to profile, not a profile of zeros
    try:
        return _profile_ydata(df)
    except Exception as exc:
        logger.info("ydata-profiling unavailable (%s); using pandas fallback.", exc)
        return _profile_pandas(df)
