"""Keyword fallback search over the built-in knowledge base."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.regulatory_rag.hits import _locator
from aaa.agents.tier1.regulatory_rag.kb import _BUILTIN_KB, _KEYWORD_MAP


def _finalize_builtin_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add the locator/provenance fields to built-in KB entries (parity with prod)."""
    finalized: list[dict[str, Any]] = []
    for hit in hits:
        ref = hit.get("ref") or hit.get("article", "")
        locator = hit.get("locator") or _locator("EU_AI_Act", ref)
        finalized.append({
            **hit,
            "ref": ref,
            "title": hit.get("title", ""),
            "source_file": hit.get("source_file", ""),
            "obligations": list(hit.get("obligations", []) or []),
            "locator": locator,
            "source_uri": hit.get("source_uri", locator),
        })
    return finalized



def builtin_search(query: str, top_k: int) -> list[dict[str, Any]]:
    """Return results from the hard-coded built-in knowledge base."""
    q_lower = query.lower()
    # Direct article match
    for keyword, article_id in _KEYWORD_MAP.items():
        if keyword in q_lower:
            hits = _BUILTIN_KB.get(article_id, [])
            if hits:
                return _finalize_builtin_hits(hits[:top_k])
    # Fallback: return all KB entries scored by simple overlap
    candidates: list[tuple[float, dict[str, Any]]] = []
    for article_id, passages in _BUILTIN_KB.items():
        for passage in passages:
            words = set(q_lower.split())
            text_words = set(passage["text"].lower().split())
            overlap = len(words & text_words) / max(len(words), 1)
            candidates.append((overlap, passage))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return _finalize_builtin_hits([p for _, p in candidates[:top_k]])
