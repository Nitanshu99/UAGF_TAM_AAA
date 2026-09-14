"""Fake Presidio NRP results over case 05's CV phrasing (T-20260913-096)."""
from __future__ import annotations

from dataclasses import dataclass

#: The sentence case 05's CVs repeat; spaCy labels both languages NORP.
CV = "warehouse operative. fluent in german and english. forklift licence."


@dataclass
class Hit:
    """The fields of a Presidio ``RecognizerResult`` the aggregation reads."""

    entity_type: str
    start: int
    end: int
    score: float = 0.85


def nrp_hits(text: str, *words: str) -> list[Hit]:
    """One NRP result per word, at its first position in *text*."""
    return [Hit("NRP", text.index(w), text.index(w) + len(w)) for w in words]
