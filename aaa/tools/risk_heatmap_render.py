"""Render a Big-4 style 5x5 risk assessment heat map."""
from __future__ import annotations

import os
from typing import Any


_LIKELIHOOD_LABELS = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
_IMPACT_LABELS = ["Negligible", "Minor", "Moderate", "Major", "Critical"]
_SEVERITY_TO_IMPACT = {
    "critical": 5,
    "major": 4,
    "minor": 3,
    "observation": 2,
}
_MATERIALITY_TO_LIKELIHOOD = {
    "material": 5,
    "possibly_material": 3,
    "not_material": 1,
}


def _cell_colour(likelihood: int, impact: int) -> str:
    score = likelihood + impact
    if score >= 8:
        return "#FF4444"
    if score in {6, 7}:
        return "#FFA500"
    return "#90EE90"


def risk_heatmap_render(findings: list[dict[str, Any]], output_path: str) -> str:
    """Render *findings* on a likelihood x impact matrix and return ``output_path``."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore
    from matplotlib.patches import Rectangle  # type: ignore

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            ax.add_patch(Rectangle(
                (likelihood - 0.5, impact - 0.5),
                1,
                1,
                facecolor=_cell_colour(likelihood, impact),
                edgecolor="white",
                linewidth=1.5,
            ))

    for finding in findings or []:
        impact = _SEVERITY_TO_IMPACT.get(str(finding.get("severity", "")).lower(), 2)
        likelihood = _MATERIALITY_TO_LIKELIHOOD.get(
            str(finding.get("materiality", "not_material")).lower(), 1,
        )
        ax.plot(likelihood, impact, "ko", markersize=5)
        ax.annotate(
            str(finding.get("finding_id", "")),
            (likelihood + 0.05, impact + 0.05),
            fontsize=7,
            color="black",
        )

    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1, 6), _LIKELIHOOD_LABELS, rotation=20, ha="right")
    ax.set_yticks(range(1, 6), _IMPACT_LABELS)
    ax.set_xlabel("Likelihood")
    ax.set_ylabel("Impact / Severity")
    ax.set_title("Risk Assessment Matrix")
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=150)
    plt.close(fig)
    return output_path


__all__ = ["risk_heatmap_render"]