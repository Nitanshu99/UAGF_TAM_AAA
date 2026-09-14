"""Part 2 of the former ``data_profile`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.data_profile.logger import _profile_ydata, logger  # noqa: F401


def _dtype_summary(df: Any) -> dict[str, int]:
    """Summarise dataframe dtypes into coarse categories.

    :param df: A ``pandas.DataFrame``.
    :returns: Category → column-count mapping.
    """
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
    return dtypes_summary
