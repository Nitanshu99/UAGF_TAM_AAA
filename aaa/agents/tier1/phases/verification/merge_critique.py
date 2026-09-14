"""Part 2 of the former ``verification`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.logger import (  # noqa: F401
    _REPORT_TIDS,
    _VERDICT_ORDER,
    _VERIFIER,
    _artefact_content,
    _artefact_uri,
    _get_verifier,
    _worse,
    logger,
)


def _merge_critique(
    crit: dict[str, Any],
    fallback_articles: list[str],
    phase_label: str,
    confidence: float,
) -> dict[str, Any]:
    """Normalise a raw Verifier critique into the stored ``verifier_critiques`` shape.

    ``article_citations`` falls back to the phase's known articles so that
    artefact admission (``_collect_admitted_articles``) keeps working even when the
    deterministic verifier does not emit citations.
    """
    notes = list(crit.get("notes") or [])
    notes.append(f"{phase_label} complete. confidence={confidence:.2f}")
    return {
        "verdict": crit.get("verdict", "accept"),
        "issues": crit.get("issues", []),
        "notes": notes,
        "article_citations": crit.get("article_citations") or list(fallback_articles),
        "rerun_required": bool(crit.get("rerun_required", False)),
        "scores": crit.get("scores", {}),
        "total_score": crit.get("total_score"),
        "llm_fallback_mode": crit.get("llm_fallback_mode"),
    }
