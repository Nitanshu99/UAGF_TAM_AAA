"""Reading an uploaded CSV's header and its column values for the data dictionary."""
from __future__ import annotations

from typing import Any


def csv_header_columns(uploaded: Any) -> list[str]:
    """Read the header row of an uploaded CSV without consuming the stream.

    :param uploaded: Streamlit ``UploadedFile`` (seekable binary stream).
    :type uploaded: Any
    :returns: Column names from the first line; empty list when unreadable.
    :rtype: list[str]
    """
    uploaded.seek(0)
    header = uploaded.readline().decode("utf-8", errors="replace").strip()
    uploaded.seek(0)
    return [col.strip().strip('"') for col in header.split(",") if col.strip()]
#: Rows sampled from an uploaded dataset for the fairness pre-check (fix F12).
#: Generous enough that cohort counts are the real ones on any evaluation set
#: this system sees, and bounded so a large upload cannot stall the wizard.
CSV_SAMPLE_ROWS = 50_000
def csv_column_values(uploaded: Any, max_rows: int = CSV_SAMPLE_ROWS
                      ) -> dict[str, list[str]]:
    """Read an uploaded CSV's columns without consuming the stream.

    Used by the data-dictionary fairness pre-check, which needs the *values* —
    whether a column is continuous, and how large its smallest cohort is — not
    just the header.

    :param uploaded: Streamlit ``UploadedFile`` (seekable binary stream).
    :param max_rows: Stop after this many data rows.
    :returns: Column name → its values; empty when the CSV cannot be read.
    """
    import csv
    import io

    uploaded.seek(0)
    text = io.StringIO(uploaded.getvalue().decode("utf-8", errors="replace"))
    uploaded.seek(0)
    columns: dict[str, list[str]] = {}
    try:
        reader = csv.DictReader(text)
        for index, row in enumerate(reader):
            if index >= max_rows:
                break
            for key, value in row.items():
                if key is not None:
                    columns.setdefault(key, []).append(value)
    except (csv.Error, UnicodeError):
        return {}
    return columns


__all__ = ["CSV_SAMPLE_ROWS", "csv_column_values", "csv_header_columns"]
