"""What the provider did not document about the dataset, named by Art. 10(2) point.

A datasheet that only leaves fields empty does not say what is missing. Case 05's
Verifier twice asked for T06's gaps "mapped to the specific Art. 10(2)
sub-paragraph" before escalating it (T-20260913-105).
"""
from __future__ import annotations

from typing import Mapping

#: Question key → the Art. 10(2) point and the element it documents.
_ELEMENTS: dict[str, tuple[str, str]] = {
    "acquisition": ("b", "how the data was acquired"),
    "timeframe": ("b", "the collection period"),
    "third_party": ("b", "third-party sources"),
    "consent": ("b", "the consent mechanism for personal data"),
    "preprocessing": ("c", "pre-processing and cleaning"),
    "labelling": ("c", "labelling and annotation"),
}
_POINTS = {"b": "Art. 10(2)(b) data collection processes and origin",
           "c": "Art. 10(2)(c) data-preparation operations"}


def undeclared_note(found: Mapping[str, object]) -> str:
    """Sentences naming each undeclared element under its Art. 10(2) point.

    :param found: Grounded answers to the T06 questions (a falsy value is unanswered).
    :returns: The note, or ``""`` when every element is answered.
    """
    missing: dict[str, list[str]] = {}
    for key, (point, element) in _ELEMENTS.items():
        if not found.get(key):
            missing.setdefault(point, []).append(element)
    if not missing:
        return ""
    listed = "; ".join(f"{_POINTS[p]}: {', '.join(e)}" for p, e in sorted(missing.items()))
    return (f"Not documented in the Annex IV dossier or the provider's documents — {listed}. "
            "No document establishes whether consent was obtained, data subjects were "
            "notified or an ethical review took place, so those fields are null (unknown).")


__all__ = ["undeclared_note"]
