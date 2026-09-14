"""Value normalisation and metric parsing for wizard form fields."""
from __future__ import annotations

import json
from typing import Any


def confidence_label(score: float) -> str:
    """Map an extraction confidence score to a human label.

    :param score: Confidence in ``[0, 1]``.
    :returns: ``"high confidence"``, ``"medium confidence"`` or ``"low confidence"``.
    """
    if score >= 0.7:
        return "high confidence"
    if score >= 0.4:
        return "medium confidence"
    return "low confidence"


def normalise_version(value: Any) -> str:
    """Return a schema-compatible version string from UI/document text.

    :param value: Raw version text (``"v2.1"`` → ``"2.1"``).
    :returns: Normalised version string.
    """
    text = str(value or "").strip()
    if len(text) > 1 and text[0].lower() == "v" and text[1].isdigit():
        return text[1:]
    return text


def numeric_metrics(value: Any, *, bounded: bool) -> dict[str, float]:
    """Keep only JSON-schema-compatible numeric metric entries.

    :param value: Candidate metrics mapping.
    :param bounded: When true, drop values outside ``[0, 1]``.
    :returns: Cleaned ``{metric: value}`` mapping.
    """
    if not isinstance(value, dict):
        return {}
    metrics: dict[str, float] = {}
    for key, raw in value.items():
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            num = float(raw)
        elif isinstance(raw, str):
            try:
                num = float(raw)
            except ValueError:
                continue
        else:
            continue
        if bounded and not 0 <= num <= 1:
            continue
        metrics[str(key)] = num
    return metrics


def parse_stage_b_metrics(raw_metrics: str) -> tuple[dict[str, float], dict[str, float] | None]:
    """Parse UI metrics JSON, accepting flat or fixture-style wrapped objects.

    :param raw_metrics: JSON text from the metrics text area.
    :returns: ``(accuracy_metrics, robustness_metrics_or_None)``.
    """
    try:
        parsed: Any = json.loads(raw_metrics)
    except json.JSONDecodeError:
        return {}, None
    if isinstance(parsed, dict) and isinstance(parsed.get("accuracy_metrics"), dict):
        accuracy = numeric_metrics(parsed["accuracy_metrics"], bounded=True)
        robustness = numeric_metrics(parsed.get("robustness_metrics"), bounded=False)
        return accuracy, robustness or None
    return numeric_metrics(parsed, bounded=True), None
