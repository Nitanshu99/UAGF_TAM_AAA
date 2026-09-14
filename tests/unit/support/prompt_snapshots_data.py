"""Expected user-message snapshots for the verifier prompt tests."""
from __future__ import annotations

EMPTY_URIS_USER_SNAPSHOT = {
    "review_request": {
        "phase_id": "P1",
        "template_id": "T02_system_card",
        "artefact_uri": "",
        "artefact_payload": {"hello": "world"},
        "declaration_summary": {},
        "prior_critique": None,
        "regulatory_hits": [],
        "evidence_uris": [],
    }
}

TWO_URIS_USER_SNAPSHOT = {
    "review_request": {
        "phase_id": "P6",
        "template_id": "T17_compliance_matrix",
        "artefact_uri": "",
        "artefact_payload": {"in_scope_articles": ["Art.9", "Art.10"]},
        "declaration_summary": {},
        "prior_critique": None,
        "regulatory_hits": [],
        "evidence_uris": [
            "evidence://eng-001/p1/T02_system_card.json",
            "evidence://eng-001/p3/T11_robustness_report.json",
        ],
    }
}
