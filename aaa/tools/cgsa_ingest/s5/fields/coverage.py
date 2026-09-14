"""Article-matrix readers for the S5 dialect: control-id lists and the Art. 9/10/13 coverage figure."""
from __future__ import annotations

from typing import Any

_CORE_ARTICLES: tuple[str, ...] = ("article_9", "article_10", "article_13")


def article_control_ids(entry: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Recover the mapped / satisfied control-id lists the contract expects.

    The dialect reports these two as counts and keeps the identities in its
    ``controls`` array, so the lists are recovered rather than reconstructed.
    """
    controls = entry.get("controls") or []
    return ([c["control_id"] for c in controls if c.get("control_id")],
            [c["control_id"] for c in controls
             if c.get("control_id") and c.get("satisfied")])


def coverage_pct(matrix: dict[str, Any]) -> float | None:
    """Percentage of Art. 9 / 10 / 13 controls meeting their thresholds.

    The contract defines the figure over exactly those three articles, which is
    why it is computed here rather than taken from the dialect's
    ``threshold_coverage_percentage`` — that one is scored over all 38 controls
    and would report a different quantity under the same name.
    """
    mapped = satisfied = 0
    for key in _CORE_ARTICLES:
        ids, ok = article_control_ids(matrix.get(key) or {})
        mapped += len(ids)
        satisfied += len(ok)
    return round(100.0 * satisfied / mapped, 1) if mapped else None
