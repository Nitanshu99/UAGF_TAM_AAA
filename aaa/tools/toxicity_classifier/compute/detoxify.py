"""Part 2 of the former ``toxicity_classifier`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.toxicity_classifier.logger import (  # noqa: F401
    _DEFAULT_SAMPLE_SIZE,
    _DEFAULT_THRESHOLD,
    _DISCRIMINATORY_KEYWORDS,
    _DISCRIMINATORY_RE,
    _assemble,
    logger,
)


def _compute_detoxify(
    predictions: Sequence[Any],
    ids: Sequence[Any],
    threshold: float,
) -> dict[str, Any]:
    """Use detoxify Detoxify("original") for per-prediction toxicity scoring."""
    from detoxify import Detoxify  # type: ignore

    model = Detoxify("original")
    entries: list[dict[str, Any]] = []
    categories_seen: set[str] = set()
    for pid, pred in zip(ids, predictions):
        text = str(pred) if pred is not None else ""
        scores = model.predict(text)
        flagged_categories = [k for k, v in scores.items() if float(v) >= threshold]
        is_flagged = bool(flagged_categories)
        if is_flagged:
            categories_seen.update(flagged_categories)
        entries.append({
            "prediction_id": str(pid),
            "text_excerpt": text[:200],
            "toxicity_score": float(scores.get("toxicity", 0.0)),
            "flagged": is_flagged,
            "flagged_categories": flagged_categories,
        })
    return _assemble(entries, sorted(categories_seen), "detoxify", threshold)
