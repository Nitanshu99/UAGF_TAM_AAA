"""Part 1 of the former ``risk_heatmap_render`` module (auto-split)."""
from __future__ import annotations

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
