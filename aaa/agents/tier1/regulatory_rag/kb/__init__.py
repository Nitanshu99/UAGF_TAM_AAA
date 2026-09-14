"""Built-in knowledge base and keyword routing for the fallback path."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.regulatory_rag.kb.core import _KB_CORE
from aaa.agents.tier1.regulatory_rag.kb.extended import _KB_EXTENDED

#: article → list of passage dicts (used when Qdrant is unreachable).
_BUILTIN_KB: dict[str, list[dict[str, Any]]] = {**_KB_CORE, **_KB_EXTENDED}

# Simple keyword → article mapping for fuzzy built-in lookup
_KEYWORD_MAP: dict[str, str] = {
    "risk management": "Art.9",
    "article 9": "Art.9",
    "data governance": "Art.10",
    "article 10": "Art.10",
    "transparency": "Art.13",
    "article 13": "Art.13",
    "conformity": "Art.43",
    "article 43": "Art.43",
    "annex iii": "Annex_III",
    "high-risk": "Annex_III",
    "gpai": "GPAI_51",
    "general purpose": "GPAI_51",
}
