"""The degraded lookup path: the built-in KB, under its own spelling of a reference."""
from __future__ import annotations

import re
from typing import Any

from aaa.agents.tier1.regulatory_rag.hits import _locator
from aaa.agents.tier1.regulatory_rag.kb import _BUILTIN_KB
from aaa.agents.tier1.regulatory_rag.lookup.annotate import DEFAULT_REGULATION, annotate

#: The built-in KB predates the corpus and refs its entries ``Art.9`` /
#: ``Annex_III`` where the corpus says ``Article 9`` / ``Annex III``. Mapping
#: between them is what lets the degraded path answer the same question.
_KB_REF = re.compile(r"^(Article|Annex)\s+(.+)$", re.IGNORECASE)


def _kb_ref(ref: str) -> str:
    """Translate a corpus ref into the built-in KB's spelling.

    :param ref: Canonical reference, e.g. ``"Article 9"`` or ``"Annex III"``.
    :type ref: str
    :returns: The KB key, e.g. ``"Art.9"`` or ``"Annex_III"``; the input
        unchanged when it matches no known shape.
    :rtype: str
    """
    match = _KB_REF.match(ref.strip())
    if not match:
        return ref
    kind, rest = match.group(1).lower(), match.group(2).strip()
    return f"Art.{rest}" if kind == "article" else f"Annex_{rest.replace(' ', '_')}"


def kb_lookup(ref: str, top_k: int) -> list[dict[str, Any]]:
    """Return the built-in KB's passages for *ref*, or ``[]``.

    The degraded path, and the one that runs wherever Qdrant is not reachable.

    :param ref: Canonical reference, e.g. ``"Article 10"``.
    :param top_k: Maximum passages to return.
    :returns: Annotated hits, in KB order.
    """
    entries = _BUILTIN_KB.get(_kb_ref(ref)) or []
    hits = []
    for i, entry in enumerate(entries[:top_k], 1):
        unit = entry.get("article", "") or ref
        locator = _locator(DEFAULT_REGULATION, ref)
        hits.append(annotate({**entry, "ref": ref, "article": unit,
                              "title": entry.get("title", ""),
                              "source_file": entry.get("source_file", ""),
                              "obligations": list(entry.get("obligations", []) or []),
                              "locator": locator, "source_uri": locator}, ref, i))
    return hits


__all__ = ["_kb_ref", "kb_lookup"]
