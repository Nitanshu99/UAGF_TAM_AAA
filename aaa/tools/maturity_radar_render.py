"""Render a governance maturity radar chart."""
from __future__ import annotations

import math
import os


_MATURITY_LABELS = {
    1: "1=Initial",
    2: "2=Developing",
    3: "3=Defined",
    4: "4=Optimised",
}


def maturity_radar_render(domain_scores: dict[str, float], output_path: str) -> str:
    """Render *domain_scores* as a filled polar radar chart and return ``output_path``."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    labels = list(domain_scores.keys()) or [f"D{i}" for i in range(1, 7)]
    values = [max(0.0, min(4.0, float(domain_scores.get(label, 0.0)))) for label in labels]
    angles = [idx / float(len(labels)) * 2 * math.pi for idx in range(len(labels))]
    plot_angles = angles + angles[:1]
    plot_values = values + values[:1]

    fig, ax = plt.subplots(figsize=(7, 6), subplot_kw=dict(polar=True))
    ax.plot(plot_angles, plot_values, color="#5b6cff", linewidth=2)
    ax.fill(plot_angles, plot_values, color="#5b6cff", alpha=0.3)
    ax.set_ylim(0, 4)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels([_MATURITY_LABELS[i] for i in [1, 2, 3, 4]], fontsize=8)
    ax.set_rlabel_position(0)
    short_labels = [label.split()[0] if label else f"D{idx + 1}" for idx, label in enumerate(labels)]
    ax.set_xticks(angles)
    ax.set_xticklabels(short_labels, fontsize=10, fontweight="bold")
    for angle, label in zip(angles, labels, strict=True):
        ax.text(angle, 4.35, label, ha="center", va="center", fontsize=7)
    composite = sum(values) / len(values) if values else 0.0
    ax.text(
        0.98,
        0.02,
        f"Composite: {composite:.1f} / 4.0",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "#cccccc"},
    )
    ax.set_title("Governance Maturity by Domain", pad=22)
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=150)
    plt.close(fig)
    return output_path


__all__ = ["maturity_radar_render"]