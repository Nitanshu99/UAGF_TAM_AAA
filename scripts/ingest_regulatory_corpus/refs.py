"""Citation canonicalisation and answer-tree traversal for the checker JSON."""
from __future__ import annotations

import re
from typing import Any

# "Article 9", "Article 9 point 2", "Article 50 point 1",
# "Annex III" / "Annex 3", "Recital 27"
REF_RE = re.compile(
    r"(Article\s+\d+(?:\s+point\s+\d+)?|Annex\s+(?:[IVX]+|\d+)|Recital\s+\d+)",
    re.IGNORECASE,
)

ARABIC_TO_ROMAN = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
    "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X",
    "11": "XI", "12": "XII", "13": "XIII",
}


def canon_ref(raw: str) -> str:
    """Canonicalise a citation: ``Article 50 point 1``, ``Annex III``, ``Recital 27``."""
    raw = re.sub(r"\s+", " ", raw).strip()
    m = re.match(r"(article|annex|recital)\s+(.+)", raw, re.IGNORECASE)
    if not m:
        return raw
    head = m.group(1).capitalize()
    tail = m.group(2)
    if head == "Annex":
        tail = ARABIC_TO_ROMAN.get(tail.strip(), tail.upper())
    else:
        tail = re.sub(r"\bpoint\b", "point", tail, flags=re.IGNORECASE)
    return f"{head} {tail}"


def parse_refs(source: str | None) -> list[str]:
    """Extract canonical Article/Recital/Annex citations from a ``source`` field."""
    if not source:
        return []
    return [canon_ref(m.group(1)) for m in REF_RE.finditer(source)]


def walk_answer(answer: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """Collect obligations/entity_types/status_changes (recurses into conditions)."""
    obligations: set[str] = set()
    entity_types: set[str] = set()
    status_changes: set[str] = set()
    if isinstance(answer.get("obligations"), list):
        obligations.update(answer["obligations"])
    if isinstance(answer.get("status_change"), str):
        status_changes.add(answer["status_change"])
    if isinstance(answer.get("visibility"), str):
        entity_types.update(s.strip() for s in answer["visibility"].split(","))
    conditions = answer.get("conditions") or {}
    if isinstance(conditions, dict):
        for cond_value in conditions.values():
            if isinstance(cond_value, dict):
                o, e, s = walk_answer(cond_value)  # recursive — same shape
                obligations |= o
                entity_types |= e
                status_changes |= s
    return obligations, entity_types, status_changes
