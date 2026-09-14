"""Shared base state for the real-auditor compliance-matrix tests."""
from __future__ import annotations

from typing import Any


def base_state(**over: Any) -> dict[str, Any]:
    """A minimal completed state with two admitted artefacts."""
    state: dict[str, Any] = {
        "engagement_id": "eng-x", "scope_gate": {},
        "verifier_critiques": {
            "T09_model_card": {"verdict": "accept",
                               "article_citations": ["Art.13", "Art.15"]},
            "T06_datasheet_for_datasets": {"verdict": "accept",
                                           "article_citations": ["Art.10"]},
        },
        "phase_artefacts": {
            "T09_model_card": {"uri": "minio://x/T09"},
            "T06_datasheet_for_datasets": {"uri": "minio://x/T06"},
        },
        "blocking_findings": [],
        "insufficient_evidence_articles": [],
        "compliance_matrix": {},
        "phase_status": {"T09_model_card": "M", "T06_datasheet_for_datasets": "M"},
        "cgsa_phase5_verdict": "PASS", "cgsa_csp_satisfiable": True,
        "intake_completeness_score": 1.0, "cgsa_payload": None,
    }
    state.update(over)
    return state
