"""Shared adverse-verdict state for the HITL verdict-case tests.

Field names mirror a real pipeline state exactly — findings live under
``blocking_findings`` and cite ``eu_ai_act_articles``. An earlier version of
this fixture invented ``findings``/``articles``; the tests passed while the
production path still produced zero cases, so the shape is copied from a real
``data/customer/*/…_audit_state.json`` record on purpose.
"""
from __future__ import annotations

FAIR_FINDING = {
    "finding_id": "P4-FAIR-AGE_GROUP",
    "description": "Output fairness across 'age_group' is FAIL (DI=0.398467).",
    "materiality": "material",
    "eu_ai_act_articles": ["Art.10§2(f)", "Art.15§1"],
    "source_phase": "P4",
    "recommendation": "Investigate and mitigate the group disparity before deployment.",
}
OBSERVATION = {
    "finding_id": "P2-NOTE", "description": "Minor note.",
    "materiality": "observation", "eu_ai_act_articles": ["Art.10"], "source_phase": "P2",
}


def state(**over) -> dict:
    """Build an adverse-verdict state with no Verifier escalations."""
    base = {
        "engagement_id": "eng-t", "final_verdict": "FAIL",
        "hitl_required": True, "hitl_reason": "Phase 4 fairness verdict is FAIL (FAIL).",
        "blocking_findings": [FAIR_FINDING, OBSERVATION],
        "verifier_critiques": {"T12_output_fairness_report": {"verdict": "accept_with_notes"}},
        "phase_artefacts": {"T12_output_fairness_report": {"uri": "minio://eng-t/T12.json"}},
    }
    base.update(over)
    return base
