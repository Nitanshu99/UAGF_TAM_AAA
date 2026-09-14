"""Part 1 of the former ``completeness_score`` module (auto-split)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


_ADMITTED_VERDICTS = {"accept", "accept_with_notes"}


_STATUS_WEIGHT: Dict[str, float] = {"M": 1.0, "O": 0.5}


def compute_completeness_score(state: AuditState) -> float:
    """
    Compute KPI 1 and write it to ``state['completeness_score']``.

    Parameters
    ----------
    state:
        Live ``AuditState`` dict.  Must contain:
        - ``phase_status``       – dict[template_id, "M" | "O" | "S"]  (CSP output)
        - ``phase_artefacts``    – dict[template_id, ArtefactRef]
        - ``verifier_critiques`` – dict[template_id, dict]

    Returns
    -------
    float
        Score in [0.0, 1.0], rounded to two decimal places.
    """
    phase_status: dict[str, str] = state.get("phase_status", {})
    phase_artefacts: dict = state.get("phase_artefacts", {})
    verifier_critiques: dict = state.get("verifier_critiques", {})

    # Templates the engagement is expected to deliver
    expected = {
        tid: status
        for tid, status in phase_status.items()
        if status in _STATUS_WEIGHT
    }

    if not expected:
        score = 0.0
        state["completeness_score"] = score
        return score

    total_weight = sum(_STATUS_WEIGHT[s] for s in expected.values())
    earned_weight = 0.0

    for tid, status in expected.items():
        # Artefact must exist AND be admitted by the Verifier
        if tid not in phase_artefacts:
            continue
        critique = verifier_critiques.get(tid, {})
        verdict = critique.get("verdict", "")
        if verdict in _ADMITTED_VERDICTS:
            earned_weight += _STATUS_WEIGHT[status]

    score = round(earned_weight / max(total_weight, 1e-9), 2)
    state["completeness_score"] = score
    return score
