"""Unit tests for the wizard model-meta helpers (CSV header capture)."""
from __future__ import annotations

from io import BytesIO

from aaa.ui.wizard.step3.csv_columns import csv_header_columns


def test_csv_header_columns_reads_and_rewinds() -> None:
    """Header columns are parsed and the stream is left at position 0."""
    stream = BytesIO(b'age_group,"sex",credit_risk\n1,2,3\n')
    assert csv_header_columns(stream) == ["age_group", "sex", "credit_risk"]
    assert stream.tell() == 0


def test_csv_header_columns_empty_stream() -> None:
    """An empty stream yields no columns."""
    assert csv_header_columns(BytesIO(b"")) == []
