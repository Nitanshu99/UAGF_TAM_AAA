"""Grouping findings onto the matrix cells and laying each cell's ids out on a ladder."""
from __future__ import annotations

from typing import Any

from aaa.tools.risk_heatmap_render.likelihood_labels import (
    _MATERIALITY_TO_LIKELIHOOD,
    _SEVERITY_TO_IMPACT,
)


def place_findings(ax: Any, findings: Any) -> None:
    """Draw each finding id on its cell.

    Findings of the same materiality and severity land on one cell, and the
    delivered report printed two ids on top of each other there. They are
    grouped and laid out on a ladder inside the cell instead.

    :param ax: The matplotlib axes the matrix is drawn on.
    :param findings: The findings to place.
    """
    # Findings of the same materiality and severity land on one cell, and the
    # delivered report printed two ids on top of each other there. They are
    # grouped and laid out on a ladder inside the cell instead.
    by_cell: dict[tuple[int, int], list[str]] = {}
    for finding in findings or []:
        impact = _SEVERITY_TO_IMPACT.get(str(finding.get("severity", "")).lower(), 2)
        likelihood = _MATERIALITY_TO_LIKELIHOOD.get(
            str(finding.get("materiality", "not_material")).lower(), 1)
        by_cell.setdefault((likelihood, impact), []).append(
            str(finding.get("finding_id", "")))

    for (likelihood, impact), ids in by_cell.items():
        step = 0.62 / max(len(ids), 1)
        top = impact + (len(ids) - 1) * step / 2.0
        # A label runs away from its marker, so in the right-hand columns it has
        # to run leftwards or it leaves the axes entirely.
        rightward = likelihood <= 3
        marker_x = likelihood - 0.34 if rightward else likelihood + 0.34
        for index, finding_id in enumerate(ids):
            y = top - index * step
            ax.plot(marker_x, y, "ko", markersize=4)
            ax.annotate(finding_id,
                        (marker_x + 0.05 if rightward else marker_x - 0.05, y),
                        fontsize=6, color="black", va="center",
                        ha="left" if rightward else "right")



__all__ = ["place_findings"]
