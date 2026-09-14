"""Whether a cell value reads as a number."""
from __future__ import annotations

from typing import Any


def _is_numeric(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False
