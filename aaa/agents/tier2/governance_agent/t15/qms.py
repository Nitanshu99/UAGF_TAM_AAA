"""The Art. 17 quality-management standard T15 records, and how it words the status.

``qms_standard_referenced`` read only ``harmonised_standards``, so a provider that
declares ISO/IEC 42001 as a reference (not a harmonised standard, not certified)
was recorded as referencing nothing; and a non-PASS rationale pointed at
"observations" that said nothing about the QMS (live run bb7837).
"""
from __future__ import annotations

from aaa.tools.term_match import match_term

#: Management-system standards a QMS can reference (AI, quality, medical devices).
_QMS_TERMS = ("42001", "9001", "13485", "quality management", "management system*")


def qms_reference(harmonised: list[str], other: list[str] | None) -> str | None:
    """The first harmonised standard, else the first declared management-system standard."""
    if harmonised:
        return str(harmonised[0])
    return next((str(s) for s in other or []
                 if any(match_term(t, str(s).lower()) for t in _QMS_TERMS)), None)


def qms_rationale(status: str, harmonised: list[str], other: list[str] | None) -> str:
    """Why Art. 17 has *status*, naming what was and was not declared."""
    if status == "PASS":
        return "Harmonised standards applied and monitoring measures documented."
    reference = qms_reference(harmonised, other)
    if harmonised:
        return f"Harmonised standard {reference} applied; monitoring measures not documented."
    if reference:
        return (f"No harmonised standard declared; the provider references {reference}, "
                "which is not a harmonised standard under Art. 40.")
    return "No harmonised or management-system standard declared in Annex IV."


__all__ = ["qms_rationale", "qms_reference"]
