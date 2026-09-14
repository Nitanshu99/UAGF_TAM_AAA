"""The in-memory compliance-checker lookup (Step 0)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CheckerLookup:
    """In-memory indexes derived from ``eu_ai_act_compliance_checker.json``."""

    #: ref ("Article 9") → {"obligations": [...], "entity_types": [...], "risk_classes": [...]}
    by_article: dict[str, dict[str, list[str]]]
    #: obligation name → metadata block from the top-level "obligations" dict
    obligations_catalogue: dict[str, dict[str, Any]]
    #: raw question records used to populate the obligations_index collection
    questions: list[dict[str, Any]]

    def for_ref(self, ref: str) -> dict[str, list[str]]:
        """Return the enrichment payload for a canonical ref (article/recital/annex)."""
        return self.by_article.get(
            ref, {"obligations": [], "entity_types": [], "risk_classes": []})
