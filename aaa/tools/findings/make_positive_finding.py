"""Part 2 of the former ``findings`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Iterable

from aaa.tools.findings.materiality import (  # noqa: F401
    BLOCKING_MATERIALITY,
    Materiality,
    make_finding,
)


def make_positive_finding(
    *,
    finding_id: str,
    description: str,
    articles: Iterable[str],
    source_phase: str,
    control_id: str | None = None,
    evidence_uris: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a positive (corroborating) finding for the T18 positive register."""
    return {
        "finding_id": finding_id,
        "description": description,
        "materiality": "observation",
        "eu_ai_act_articles": list(articles),
        "source_phase": source_phase,
        "control_id": control_id,
        "evidence_uris": list(evidence_uris or []),
    }


def collect_evidence_uris(*sources: Any) -> list[str]:
    """Flatten heterogeneous evidence sources into a de-duplicated URI list.

    Each *source* may be a single URI string, a list of URI strings, or a list of
    retrieval hit dicts (``client_doc_search`` / ``RegulatoryRAG.search``) from
    which ``source_uri`` (falling back to ``locator``) is read. Order is preserved;
    empties are dropped. Used by phase agents to ground every finding in the
    provenance they actually inspected.
    """
    seen: set[str] = set()
    out: list[str] = []

    def _add(uri: Any) -> None:
        if isinstance(uri, str) and uri and uri not in seen:
            seen.add(uri)
            out.append(uri)

    for source in sources:
        if source is None:
            continue
        items = source if isinstance(source, (list, tuple)) else [source]
        for item in items:
            if isinstance(item, dict):
                _add(item.get("source_uri") or item.get("locator") or "")
            else:
                _add(item)
    return out
