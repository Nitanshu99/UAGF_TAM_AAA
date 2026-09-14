"""Part 2 of the former ``hitl_review`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.hitl_review.tid_phase import (  # noqa: F401
    _HITL_VERDICTS,
    _TID_PHASE,
    DECISION_ACCEPT,
    DECISION_OVERRIDE,
    DECISION_UPHOLD,
    _now,
)


def _evidence_for_case(state: dict, tid: str, critique: dict) -> list[str]:
    """Collect the evidence the auditor relied on for this artefact.

    The artefact's own persisted URI plus any evidence URIs attached to the
    articles it cites, de-duplicated and capped for readability.
    """
    seen: set[str] = set()
    out: list[str] = []

    def _add(uri: Any) -> None:
        if isinstance(uri, str) and uri and uri not in seen:
            seen.add(uri)
            out.append(uri)

    ref = (state.get("phase_artefacts", {}) or {}).get(tid)
    if isinstance(ref, dict):
        _add(ref.get("uri", ""))

    article_evidence = state.get("article_evidence", {}) or {}
    for article in critique.get("article_citations", []) or []:
        ev = article_evidence.get(article, {}) or {}
        for uri in ev.get("evidence_uris", []) or []:
            _add(uri)
    return out[:10]


def hitl_cases(state: dict) -> list[str]:
    """Template ids the Verifier escalated to HITL, in template order."""
    critiques = state.get("verifier_critiques", {}) or {}
    return [tid for tid, c in critiques.items() if c.get("verdict") in _HITL_VERDICTS]
