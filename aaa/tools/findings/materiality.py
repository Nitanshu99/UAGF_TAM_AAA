"""Part 1 of the former ``findings`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Iterable

# One vocabulary, defined with the state types that carry it.
from aaa.platform.state.findings import Materiality

BLOCKING_MATERIALITY = "material"


def make_finding(
    *,
    finding_id: str,
    description: str,
    materiality: Materiality,
    articles: Iterable[str],
    source_phase: str,
    recommendation: str = "",
    control_id: str | None = None,
    declared: Any = None,
    observed: Any = None,
    evidence_uris: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a canonical finding dict consumed by the report + compliance matrix."""
    return {
        "finding_id": finding_id,
        "description": description,
        "materiality": materiality,
        "eu_ai_act_articles": list(articles),
        "source_phase": source_phase,
        "recommendation": recommendation,
        "control_id": control_id,
        "declared": declared,
        "observed": observed,
        "evidence_uris": list(evidence_uris or []),
    }
