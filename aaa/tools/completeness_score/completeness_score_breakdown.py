"""Part 2 of the former ``completeness_score`` module (auto-split)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from aaa.tools.completeness_score.admitted_verdicts import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _STATUS_WEIGHT,
    compute_completeness_score,
)

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def completeness_score_breakdown(state: AuditState) -> dict:
    """
    Return a per-template breakdown for T17/T18 report embedding.

    Returns
    -------
    dict with keys:
        score        – overall KPI 1 float
        expected     – list of {template_id, status, weight, admitted}
        total_weight – sum of all expected weights
        earned_weight– sum of admitted weights
    """
    phase_status: dict[str, str] = state.get("phase_status", {})
    phase_artefacts: dict = state.get("phase_artefacts", {})
    verifier_critiques: dict = state.get("verifier_critiques", {})

    rows = []
    total_weight = 0.0
    earned_weight = 0.0

    for tid, status in phase_status.items():
        if status not in _STATUS_WEIGHT:
            continue
        w = _STATUS_WEIGHT[status]
        total_weight += w
        admitted = False
        if tid in phase_artefacts:
            verdict = verifier_critiques.get(tid, {}).get("verdict", "")
            admitted = verdict in _ADMITTED_VERDICTS
        if admitted:
            earned_weight += w
        rows.append({"template_id": tid, "status": status, "weight": w, "admitted": admitted})

    score = round(earned_weight / max(total_weight, 1e-9), 2)
    return {
        "score": score,
        "expected": rows,
        "total_weight": round(total_weight, 4),
        "earned_weight": round(earned_weight, 4),
    }
