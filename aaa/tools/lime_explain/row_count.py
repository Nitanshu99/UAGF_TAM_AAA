"""Part 3 of the former ``lime_explain`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.lime_explain.explain.lime import _explain_lime  # noqa: F401
from aaa.tools.lime_explain.logger import (  # noqa: F401
    _DEFAULT_NUM_FEATURES,
    _DEFAULT_NUM_INSTANCES,
    logger,
)


def _row_count(X: Any) -> int:
    try:
        return int(len(X))
    except Exception:
        return 0


def _is_numeric(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False
