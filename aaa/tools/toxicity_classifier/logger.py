"""Part 1 of the former ``toxicity_classifier`` module (auto-split)."""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


_DEFAULT_SAMPLE_SIZE = 200


_DEFAULT_THRESHOLD = 0.50


_DISCRIMINATORY_KEYWORDS = [
    r"\bhate\b", r"\bracist\b", r"\bsexist\b", r"\bbigot(ed|ry)?\b",
    r"\bslur\b", r"\bdiscriminat(e|ion|ory)\b",
    r"\binferior\b", r"\bsupremac(y|ist)\b",
]


_DISCRIMINATORY_RE = re.compile("|".join(_DISCRIMINATORY_KEYWORDS), re.IGNORECASE)


def _assemble(
    entries: list[dict[str, Any]],
    categories: list[str],
    tool: str,
    threshold: float | None,
) -> dict[str, Any]:
    """Common assembly: derive flagged count, pct, verdict.

    ``threshold`` is recorded only when one was applied — a keyword screen applies none.
    """
    sample_size = len(entries)
    flagged_count = sum(1 for e in entries if e["flagged"])
    flagged_pct = (100.0 * flagged_count / sample_size) if sample_size else None
    if flagged_pct is None:
        verdict = "NOT_TESTED"
    elif flagged_count == 0:
        verdict = "PASS"
    elif flagged_pct <= 5.0:
        verdict = "PASS_WITH_OBSERVATIONS"
    else:
        verdict = "FAIL"
    result: dict[str, Any] = {
        "sample_size": sample_size,
        "flagged_count": flagged_count,
        "flagged_pct": None if flagged_pct is None else round(flagged_pct, 4),
        "entries": entries,
        "categories_observed": categories,
        "verdict": verdict,
        "tool": tool,
    }
    if threshold is not None:
        result["threshold"] = threshold
    return result
