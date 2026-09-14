"""Minimal duck-typed empty DataFrame for no-pandas environments."""
from __future__ import annotations

from typing import Any


class _ZeroSeries:
    """A series stub whose aggregate is always zero."""

    def sum(self) -> int:
        """Return the aggregate, always zero for the stub."""
        return 0


class _EmptyDataFrame:
    """Ultra-minimal DataFrame stub for environments without pandas."""

    def __init__(self) -> None:
        self.columns: list[str] = []
        self.shape: tuple[int, int] = (0, 0)

    def __len__(self) -> int:
        return 0

    def head(self, n: int) -> "_EmptyDataFrame":
        """Return itself; the stub is always empty."""
        return self

    def memory_usage(self, deep: bool = False) -> Any:
        """Return a zero-valued series stub."""
        return _ZeroSeries()

    def duplicated(self) -> Any:
        """Return a zero-valued series stub (no duplicates)."""
        return _ZeroSeries()


def empty_frame() -> Any:
    """Return an empty DataFrame (or duck-typed stub) for tool calls."""
    try:
        import pandas as pd  # type: ignore
        return pd.DataFrame()
    except ImportError:
        return _EmptyDataFrame()
