"""
KPI 1 — Completeness Score (§9.1)

Fraction of expected artefact templates that are present, schema-valid, and
admitted by the Verifier for the given engagement.

  expected = {tid : status in {M, O} from phase_status CSP output}
  delivered = {tid : verifier verdict in {accept, accept_with_notes}}
  score = |delivered ∩ expected| / max(|expected|, 1)

Mandatory templates (status=M) have weight 1.0; optional (status=O) weight 0.5.
Written to AuditState.completeness_score.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from src.platform.state import AuditState

# Accepted verdicts from the Verifier
_ADMITTED_VERDICTS = {"accept", "accept_with_notes"}

# Weight per phase-status designation
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
