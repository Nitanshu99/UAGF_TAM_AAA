"""
KPI 2 — Regulatory Coverage % (§9.1)

Fraction of in-scope EU AI Act articles for which the audit produces at least
one admitted evidence artefact with a verifiable RAG-cited regulatory clause.

  in_scope  = ARTICLE_SET[risk_tier]   (see table below)
  covered   = {a ∈ in_scope : ≥1 admitted artefact cites article a}
  pct       = 100 * |covered| / max(|in_scope|, 1)

Written to AuditState.regulatory_coverage_pct.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, FrozenSet

if TYPE_CHECKING:
    from src.platform.state import AuditState

# In-scope article sets per risk tier (§9.1 table)
ARTICLE_SET: dict[str, FrozenSet[str]] = {
    "high": frozenset({
        "Art.9", "Art.10", "Art.13", "Art.14", "Art.15", "Art.17", "Art.43",
        "Annex_III", "Annex_IV",
    }),
    "high_llm": frozenset({
        "Art.9", "Art.10", "Art.13", "Art.14", "Art.15", "Art.17", "Art.43",
        "Annex_III", "GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55",
    }),
    "limited": frozenset({
        "Art.13", "Art.50", "Annex_IV",
    }),
    "minimal": frozenset({
        "Art.50",
    }),
    "gpai": frozenset({
        "GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55",
        "Annex_XI", "Annex_XII",
    }),
    "prohibited": frozenset(),
}

_ADMITTED_VERDICTS = {"accept", "accept_with_notes"}


def _resolve_article_set(state: AuditState) -> FrozenSet[str]:
    """Choose the correct in-scope article set given state."""
    tier = state.get("risk_tier", state.get("declared_risk_tier", "minimal"))
    is_llm = state.get("is_llm_or_agentic", False)

    if tier == "high" and is_llm:
        return ARTICLE_SET["high_llm"]
    return ARTICLE_SET.get(tier, frozenset())


def compute_regulatory_coverage_pct(state: AuditState) -> float:
    """
    Compute KPI 2 and write it to ``state['regulatory_coverage_pct']``.

    Coverage is determined by examining ``compliance_matrix`` entries:
    an article is *covered* when its verdict is not "PENDING" / "NOT_APPLICABLE"
    and at least one admitted artefact in ``phase_artefacts`` cites it via
    ``verifier_critiques[tid]['article_citations']`` (list[str]).

    Parameters
    ----------
    state : AuditState

    Returns
    -------
    float  in [0.0, 100.0], rounded to one decimal place.
    """
    in_scope = _resolve_article_set(state)
    if not in_scope:
        state["regulatory_coverage_pct"] = 100.0
        return 100.0

    verifier_critiques: dict = state.get("verifier_critiques", {})
    phase_artefacts: dict = state.get("phase_artefacts", {})

    # Collect all articles cited by admitted artefacts
    cited_articles: set[str] = set()
    for tid in phase_artefacts:
        critique = verifier_critiques.get(tid, {})
        if critique.get("verdict", "") not in _ADMITTED_VERDICTS:
            continue
        for cite in critique.get("article_citations", []):
            cited_articles.add(str(cite).strip())

    # Fall back to compliance_matrix verdicts if citations unavailable
    compliance_matrix: dict = state.get("compliance_matrix", {})
    for article, verdict in compliance_matrix.items():
        if verdict not in ("PENDING", "NOT_APPLICABLE", None):
            cited_articles.add(article)

    covered = in_scope & cited_articles
    pct = round(100.0 * len(covered) / max(len(in_scope), 1), 1)
    state["regulatory_coverage_pct"] = pct
    return pct


def regulatory_coverage_breakdown(state: AuditState) -> dict:
    """
    Return a per-article breakdown for T17/T18 report embedding.

    Returns
    -------
    dict with keys:
        regulatory_coverage_pct  – overall KPI 2 float
        in_scope                 – sorted list of article IDs
        covered                  – sorted list of covered article IDs
        missing                  – sorted list of uncovered article IDs
    """
    in_scope = _resolve_article_set(state)
    verifier_critiques: dict = state.get("verifier_critiques", {})
    phase_artefacts: dict = state.get("phase_artefacts", {})
    compliance_matrix: dict = state.get("compliance_matrix", {})

    cited_articles: set[str] = set()
    for tid in phase_artefacts:
        critique = verifier_critiques.get(tid, {})
        if critique.get("verdict", "") not in _ADMITTED_VERDICTS:
            continue
        for cite in critique.get("article_citations", []):
            cited_articles.add(str(cite).strip())
    for article, verdict in compliance_matrix.items():
        if verdict not in ("PENDING", "NOT_APPLICABLE", None):
            cited_articles.add(article)

    covered = in_scope & cited_articles
    missing = in_scope - covered
    pct = round(100.0 * len(covered) / max(len(in_scope), 1), 1)

    return {
        "regulatory_coverage_pct": pct,
        "in_scope": sorted(in_scope),
        "covered": sorted(covered),
        "missing": sorted(missing),
    }
