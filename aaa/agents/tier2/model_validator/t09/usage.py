"""The T09 intended-use block and the card's fixed attribution notes."""
from __future__ import annotations

from typing import Any

#: Fix 47 (R15), found auditing the templates for hard-coded compliance sentences:
#: this asserted that the system *is* subject to an ongoing Art. 9 risk-management
#: process — a statement about the client that Phase 3 never checked. Art. 9 is
#: Phase 5's, through the CGSA payload.
ETHICAL_CONSIDERATIONS = (
    "Model-level ethical risks are recorded in known_limitations. The "
    "Art. 9 risk-management system is assessed in Phase 5 "
    "(T14_governance_findings) and is not evaluated here.")

ART13_NOTES = ("Model card populated from Annex IV dossier + metric_suite. "
               "Phase 3 ModelValidator — Art. 13 §3, Art. 15.")


def intended_use_section(t01a: dict[str, Any]) -> dict[str, Any]:
    """The declared intended purpose, and the uses outside it.

    :param t01a: T01a triage artefact.
    """
    return {
        "primary_use_cases": [t01a.get(
            "intended_purpose", "Intended purpose inherited from system card.")],
        "out_of_scope_use_cases": [
            "Any use outside the declared intended purpose.",
            "Any use violating EU AI Act Art. 5 prohibitions.",
        ],
    }


__all__ = ["ART13_NOTES", "ETHICAL_CONSIDERATIONS", "intended_use_section"]
