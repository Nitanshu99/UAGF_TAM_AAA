"""The profile of a dataset that was never loaded: every count is null.

Phase 2 used to profile an empty stand-in frame when the dataset could not be
loaded, and T07 then reported ``num_rows: 0`` — a count of the stand-in, not of
the provider's data (T-20260913-062).
"""
from __future__ import annotations

from typing import Any


def not_profiled() -> dict[str, Any]:
    """Return a T07 ``dataset_summary`` that states nothing was measured.

    :returns: The block with every measurement null.
    """
    return {
        "num_rows": None,
        "num_columns": None,
        "data_types_summary": {},
        "duplicate_rows": None,
        "duplicate_rows_pct": None,
        "memory_usage_bytes": None,
        "profiling_tool": None,
        "profiling_tool_version": None,
    }
