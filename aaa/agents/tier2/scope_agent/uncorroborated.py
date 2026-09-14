"""A declared Annex III section the intake text does not evidence, said and recorded.

Classification under Art. 6(2) is the provider's to make, so the audit keeps a declared
section and its high-risk tier. It must not call that tier verified: case 03 declared
Annex III §2 (critical infrastructure) for harbour-crane telemetry, the intake names
none of §2's use cases, and T03 still read "Verified risk tier: high" (T-20260914-004).
"""
from __future__ import annotations

from typing import Any

from aaa.tools.annex_iii_classify import NO_KEYWORD_EVIDENCE
from aaa.tools.findings import make_finding


def uncorroborated(entries: list[Any]) -> list[Any]:
    """Declared entries whose section the intake text offers no term for."""
    return [e for e in entries if e.get("provenance") == "client_declared"
            and e.get("use_case_marker") == NO_KEYWORD_EVIDENCE]


def _names(entries: list[Any]) -> str:
    return "; ".join(f"Annex III §{e['annex_iii_section']} ({e.get('section_title')})"
                     for e in entries)


def uncorroborated_note(entries: list[Any], tier: str) -> str:
    """The T03 sentence saying the tier stands on a declaration the intake does not support."""
    missing = uncorroborated(entries)
    if not missing:
        return ""
    return (f" The {tier} tier rests on the provider's declaration of {_names(missing)}; the "
            "intake text names no use case of that section, so the audit has not corroborated "
            "the classification.")


def uncorroborated_finding(entries: list[Any]) -> dict[str, Any] | None:
    """A possibly-material observation asking the provider to justify the declared section."""
    missing = uncorroborated(entries)
    if not missing:
        return None
    return make_finding(
        finding_id="P1-ANNEX-III-UNCORROBORATED",
        description=(f"Declared {_names(missing)} is not corroborated: the intake text names no "
                     "use case of that section. The high-risk classification is kept as "
                     "declared under Art. 6(2)."),
        materiality="possibly_material", articles=["Art.6", "Annex_III"], source_phase="P1",
        recommendation="State which use case of the declared Annex III section the system is "
                       "intended for, with the documentation that shows it.")


__all__ = ["uncorroborated", "uncorroborated_finding", "uncorroborated_note"]
