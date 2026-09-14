"""Part 2 of the former ``risk_heatmap_render`` module (auto-split)."""
from __future__ import annotations

import os
from typing import Any

from aaa.tools.risk_heatmap_render.cells import place_findings
from aaa.tools.risk_heatmap_render.likelihood_labels import (  # noqa: F401
    _IMPACT_LABELS,
    _LIKELIHOOD_LABELS,
    _MATERIALITY_TO_LIKELIHOOD,
    _SEVERITY_TO_IMPACT,
    _cell_colour,
)


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
                (likelihood - 0.5, impact - 0.5), 1, 1,
                facecolor=_cell_colour(likelihood, impact),
                edgecolor="white", linewidth=1.5))

    place_findings(ax, findings)
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
