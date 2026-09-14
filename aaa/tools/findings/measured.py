"""Render a measurement for a narrative line, or say it was not measured.

A missing value used to be formatted with a default — ``get(key, 0)`` printed
"Missingness overall: 0.0%" for a dataset that was never loaded
(T-20260913-062). Narratives now print the value only when one was taken.
"""
from __future__ import annotations

from typing import Any

NOT_MEASURED = "not measured"


def measured(value: Any, spec: str = "", unit: str = "") -> str:
    """Format *value* with *spec* and *unit*, or ``"not measured"`` when it is ``None``.

    :param value: The measured value, or ``None`` when nothing was measured.
    :param spec: A format spec such as ``".1f"``.
    :param unit: A suffix such as ``"%"``.
    :returns: The rendered text.
    """
    if value is None:
        return NOT_MEASURED
    return f"{value:{spec}}{unit}"
