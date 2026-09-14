"""Part 3 of the former ``toxicity_classifier`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.toxicity_classifier.compute.detoxify import _compute_detoxify  # noqa: F401
from aaa.tools.toxicity_classifier.logger import (  # noqa: F401
    _DEFAULT_SAMPLE_SIZE,
    _DEFAULT_THRESHOLD,
    _DISCRIMINATORY_KEYWORDS,
    _DISCRIMINATORY_RE,
    _assemble,
    logger,
)


def _compute_python(
    predictions: Sequence[Any],
    ids: Sequence[Any],
) -> dict[str, Any]:
    """Regex keyword screen used when detoxify is unavailable.

    A keyword hit is an observation, so it is flagged; but a screen is not a
    classifier, so it writes no toxicity score (it once wrote 1.0 / 0.0) and a
    sample with no hit is ``NOT_TESTED``, not ``PASS`` (T-20260913-063). Nor does
    it apply a probability threshold, so none is recorded (T-20260914-060).
    """
    entries: list[dict[str, Any]] = []
    categories_seen: set[str] = set()
    for pid, pred in zip(ids, predictions):
        text = str(pred) if pred is not None else ""
        match = _DISCRIMINATORY_RE.search(text)
        flagged = bool(match)
        flagged_categories = ["discriminatory_keyword"] if flagged else []
        if flagged:
            categories_seen.update(flagged_categories)
        entries.append({
            "prediction_id": str(pid),
            "text_excerpt": text[:200],
            "toxicity_score": None,
            "flagged": flagged,
            "flagged_categories": flagged_categories,
        })
    result = _assemble(entries, sorted(categories_seen), "pure-python-keyword", None)
    if not result["flagged_count"]:
        result["verdict"] = "NOT_TESTED"
    return result


def _empty_result() -> dict[str, Any]:
    """Return the result for a sample that was never scored.

    No classifier ran, so no threshold was applied: writing the tool's default here
    read in T13 as a configured cut-off beside ``tool: null`` (T-20260914-060).
    """
    return {
        "sample_size": 0,
        "flagged_count": 0,
        "flagged_pct": None,
        "entries": [],
        "categories_observed": [],
        "verdict": "NOT_TESTED",
        "tool": None,
    }
