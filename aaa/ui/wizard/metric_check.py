"""Saying which declared metrics the wizard will not record, instead of dropping them."""
from __future__ import annotations

import json
from typing import Any

from aaa.ui.wizard.parsing import numeric_metrics


def discarded_metrics(raw_metrics: str) -> list[str]:
    """Metric names the performance block names but :func:`parse_stage_b_metrics` drops.

    A flat object keeps only numbers in ``[0, 1]`` as accuracy metrics, so a latency
    of 412 ms disappeared without a word. The wizard shows these names instead.

    :param raw_metrics: JSON text from the metrics text area.
    :returns: Dropped names, in the order given; ``[]`` for unparseable text.
    """
    try:
        parsed: Any = json.loads(raw_metrics)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, dict):
        return []
    nested = parsed.get("accuracy_metrics")
    block: dict[str, Any] = nested if isinstance(nested, dict) else parsed
    kept = numeric_metrics(block, bounded=True)
    return [str(key) for key in block if str(key) not in kept and key != "robustness_metrics"]


__all__ = ["discarded_metrics"]
