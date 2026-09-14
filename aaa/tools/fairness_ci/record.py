"""The interval record a fairness metric carries in T12."""
from __future__ import annotations

from typing import Any

from aaa.tools.fairness_ci.logger import CONFIDENCE_LEVEL


def interval(found: dict[str, Any], method: str) -> dict[str, Any]:
    """The deciding pair's interval, with the pair and how many pairs were compared.

    :param found: A :mod:`~aaa.tools.fairness_ci.decision` result.
    :param method: The interval estimator's name.
    """
    low, high = found["interval"]
    return {"low": None if low is None else round(low, 6),
            "high": None if high is None else round(high, 6),
            "level": CONFIDENCE_LEVEL, "groups": [found["group"], found["baseline"]],
            "comparisons": found["comparisons"],
            "method": f"{method}; Bonferroni-adjusted over {found['comparisons']} pair(s)"}


__all__ = ["interval"]
