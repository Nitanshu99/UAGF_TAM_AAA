"""What Phase 2 actually measured, for the datasheet to report.

T06 was built from the dossier alone, reading ``training_dataset_size`` — a key
no contract defines — so ``num_instances`` was ``0`` for every engagement, while
the same phase had loaded the evaluation CSV and T07 reported its 600 rows
(T-20260913-009). A datasheet describes the dataset actually examined (Gebru et
al., 2021), so the counts come from here or are ``None``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetMeasurement:
    """Counts taken from the dataset Phase 2 loaded."""

    dataset_uri: str | None
    num_rows: int
    num_columns: int
    columns: tuple[str, ...]
    overall_missing_pct: float | None
    missing_columns: tuple[str, ...]


def measure(df: Any, data_available: bool, dataset_uri: str | None,
            miss_result: dict[str, Any]) -> DatasetMeasurement | None:
    """The measurement, or ``None`` when no dataset was loaded.

    :param df: The frame the Phase 2 tools ran on.
    :param data_available: Whether that frame is the real dataset.
    :param dataset_uri: The URI it was loaded from.
    :param miss_result: ``missingness_scan`` output for the same frame.
    :returns: A :class:`DatasetMeasurement`, never a stub of zeros.
    """
    if not data_available or df is None:
        return None
    columns = tuple(str(c) for c in df.columns)
    missing = tuple(str(c.get("column_name")) for c in miss_result.get("columns") or []
                    if c.get("missing_count"))
    return DatasetMeasurement(dataset_uri, int(len(df)), len(columns), columns,
                              _pct(miss_result.get("overall_missingness_pct")), missing)


def _pct(value: Any) -> float | None:
    """The scanned share, or ``None`` — never a 0.0 standing in for no scan."""
    return None if value is None else float(value)


__all__ = ["DatasetMeasurement", "measure"]
