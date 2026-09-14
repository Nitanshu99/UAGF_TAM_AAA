"""Render a governance maturity radar chart."""
from __future__ import annotations

import math
import os
import textwrap

_MATURITY_LABELS = {
    1: "1 Initial",
    2: "2 Developing",
    3: "3 Defined",
    4: "4 Optimised",
}

#: Characters per line before a domain name wraps. Six spokes on an 18 cm-wide
#: figure leave roughly this much room before neighbouring labels collide.
_WRAP = 16


def _spoke_labels(labels: list[str]) -> list[str]:
    """Wrap each domain name onto short lines so neighbours do not collide."""
    return ["\n".join(textwrap.wrap(label, _WRAP)) or label for label in labels]


def maturity_radar_render(domain_scores: dict[str, float], output_path: str) -> str:
    """Render *domain_scores* as a filled polar radar chart and return ``output_path``.

    Finding Q16: the chart used to draw each domain twice — a bold short code on
    the rim and the full name just outside it, at the *same* angle — and put the
    radial scale on the 0 degree axis, which is where the first spoke label sits.
    Every label collided with something. One label per spoke now, wrapped, with
    the scale moved into the gap between two spokes and the composite annotation
    below the axes instead of on top of the last one.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    labels = list(domain_scores.keys()) or [f"D{i}" for i in range(1, 7)]
    values = [max(0.0, min(4.0, float(domain_scores.get(label, 0.0)))) for label in labels]
    angles = [idx / float(len(labels)) * 2 * math.pi for idx in range(len(labels))]
    plot_angles = angles + angles[:1]
    plot_values = values + values[:1]

    fig, ax = plt.subplots(figsize=(7.2, 6.4), subplot_kw={"polar": True})
    ax.plot(plot_angles, plot_values, color="#5b6cff", linewidth=2)
    ax.fill(plot_angles, plot_values, color="#5b6cff", alpha=0.3)
    ax.set_ylim(0, 4)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels([_MATURITY_LABELS[i] for i in [1, 2, 3, 4]], fontsize=7,
                       color="#64748b")
    # Half a sector round from the first spoke: the widest gap available.
    gap = math.degrees(angles[1] / 2.0) if len(angles) > 1 else 45.0
    # set_rlabel_position exists on polar Axes but not in matplotlib's stubs.
    ax.set_rlabel_position(gap)  # pyright: ignore[reportAttributeAccessIssue]
    ax.set_xticks(angles)
    ax.set_xticklabels(_spoke_labels(labels), fontsize=8)
    ax.tick_params(axis="x", pad=14)
    composite = sum(values) / len(values) if values else 0.0
    ax.set_title("Governance Maturity by Domain", pad=26)
    fig.text(0.5, 0.02, f"Composite: {composite:.1f} / 4.0", ha="center", va="bottom",
             fontsize=9, color="#0f172a")
    fig.subplots_adjust(top=0.86, bottom=0.12, left=0.14, right=0.86)
    fig.savefig(output_path, format="png", dpi=150)
    plt.close(fig)
    return output_path


__all__ = ["maturity_radar_render"]
