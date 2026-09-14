"""Which rows and values of a frame the PII scan reads, and what a column holds."""
from __future__ import annotations

from typing import Any

from aaa.tools.pii_scan.logger import SAMPLE_SEED


def _sample(df: Any, sample_rows: int) -> Any:
    """A seeded random sample; the first rows of a sorted file are not representative."""
    return df if len(df) <= sample_rows else df.sample(n=sample_rows, random_state=SAMPLE_SEED)


def _column_cells(sample: Any, col: Any) -> list[str]:
    """The column's non-empty values as text."""
    return [text for text in (str(v) for v in sample[col].dropna().tolist()) if text.strip()]


def _is_numeric(series: Any) -> bool:
    """Whether a column holds numbers (its dtype, not its text)."""
    from pandas.api.types import is_numeric_dtype  # type: ignore

    return bool(is_numeric_dtype(series))


__all__ = ["_column_cells", "_is_numeric", "_sample"]
