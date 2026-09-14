"""The provider's declared Art. 6(3) derogation, carried onto each declared Annex III use."""
from __future__ import annotations

from typing import Any


def stamp_declared_derogation(entries: list[Any], t01a: dict[str, Any]) -> None:
    """Record the Stage A derogation claim on every client-declared entry, in place.

    The classifier set ``derogation_claimed: false`` on every entry and cannot know
    the claim; Stage A carries it system-wide (T-20260913-037).

    :param entries: Annex III entries from ``annex_iii_classify``.
    :param t01a: The Stage A triage artefact.
    """
    claimed = bool(t01a.get("art6_derogation_claimed"))
    rationale = t01a.get("art6_derogation_rationale") or None
    for entry in entries:
        if entry["provenance"] == "client_declared":
            entry["derogation_claimed"] = claimed
            entry["derogation_rationale"] = rationale


__all__ = ["stamp_declared_derogation"]
