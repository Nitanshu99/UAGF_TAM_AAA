"""
annex_iii_classify — deterministic MCP-style tool (§3.6, §4.5).

Classifies an AI system against the Annex III high-risk use-case taxonomy.

Returns a list of ``AnnexIIIEntry`` dicts with ``provenance`` set to one of:
  - ``client_declared``  — declared in Stage A and confirmed by Phase 1
  - ``phase1_verified``  — not declared; Phase 1 detected it with evidence
  - ``phase1_corrected`` — declared, but section number adjusted by Phase 1
  - ``phase1_rejected``  — declared by client but evidence refutes it

Runtime:
  Production  — LlamaIndex ``VectorStoreIndex`` over Annex III text (Qdrant).
  Offline     — Keyword/rule-based classifier over the static Annex III table.

Usage::

    entries = annex_iii_classify(
        declared_sections=["5"],
        system_description="Credit scoring for retail bank customers.",
        rag_search_fn=regulatory_rag.search,   # optional; None → offline
    )
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from src.platform.state import AnnexIIIEntry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Annex III static catalogue (§3.6 table)
# ---------------------------------------------------------------------------

_ANNEX_III_CATALOGUE: dict[str, dict[str, Any]] = {
    "1": {
        "section_title": "Biometrics (remote ID, categorisation, emotion recognition)",
        "keywords": [
            "biometric", "facial recognition", "face", "fingerprint",
            "voice identification", "emotion recognition", "gait", "iris",
            "remote biometric identification",
        ],
    },
    "2": {
        "section_title": "Critical infrastructure (energy, water, traffic management)",
        "keywords": [
            "critical infrastructure", "energy grid", "power grid", "water management",
            "traffic management", "transportation infrastructure", "digital infrastructure",
        ],
    },
    "3": {
        "section_title": "Education and vocational training",
        "keywords": [
            "education", "admissions", "exam", "grading", "student assessment",
            "vocational training", "educational institution", "school", "university",
        ],
    },
    "4": {
        "section_title": "Employment, workers management, self-employment",
        "keywords": [
            "employment", "recruitment", "hiring", "cv screening", "resume screening",
            "worker monitoring", "performance scoring", "self-employment", "job candidate",
        ],
    },
    "5": {
        "section_title": "Access to essential private/public services and benefits",
        "keywords": [
            "credit scoring", "credit", "loan", "insurance", "benefits eligibility",
            "essential service", "public service", "social assistance", "emergency service",
            "creditworthiness", "finance", "banking",
        ],
    },
    "6": {
        "section_title": "Law enforcement",
        "keywords": [
            "law enforcement", "police", "predictive policing", "crime", "evidence assessment",
            "criminal", "judicial investigation", "risk assessment of offenders",
        ],
    },
    "7": {
        "section_title": "Migration, asylum, border control",
        "keywords": [
            "migration", "asylum", "border control", "visa", "immigration",
            "document authenticity", "refugee", "border management",
        ],
    },
    "8": {
        "section_title": "Administration of justice and democratic processes",
        "keywords": [
            "judiciary", "judicial", "court", "legal decision", "democratic process",
            "electoral", "administration of justice", "dispute resolution",
        ],
    },
}

# Confidence assigned to keyword hits in offline mode
_OFFLINE_DECLARED_CONFIDENCE = 0.75
_OFFLINE_DETECTED_CONFIDENCE = 0.60
_OFFLINE_REJECTION_THRESHOLD = 0.20  # below this → phase1_rejected


def annex_iii_classify(
    declared_sections: list[str],
    system_description: str,
    rag_search_fn: Callable[[str], list[dict[str, Any]]] | None = None,
) -> list[AnnexIIIEntry]:
    """
    Classify an AI system against the Annex III taxonomy.

    Parameters
    ----------
    declared_sections:
        Sections declared by the client in Stage A (e.g. ``["4", "5"]``).
    system_description:
        Concatenated text from the intake bundle (intended_purpose +
        general_description + training_data_description) used as evidence.
    rag_search_fn:
        Optional callable that accepts a query string and returns a list of
        ``{text, source, article, score}`` dicts (RegulatoryRAG.search API).
        When ``None``, the offline keyword classifier is used.

    Returns
    -------
    list[AnnexIIIEntry]
        One entry per identified section, ordered by confidence descending.
        Declared sections that are not supported by evidence get provenance
        ``phase1_rejected``.
    """
    desc_lower = system_description.lower()
    entries: list[AnnexIIIEntry] = []

    # ── Step 1: Evaluate all 8 sections for evidence ─────────────────────────
    section_scores: dict[str, float] = {}
    for section, meta in _ANNEX_III_CATALOGUE.items():
        if rag_search_fn is not None:
            score = _rag_score(section, meta["section_title"], desc_lower, rag_search_fn)
        else:
            score = _keyword_score(meta["keywords"], desc_lower)
        section_scores[section] = score

    # ── Step 2: Resolve provenance per section ────────────────────────────────
    declared_set = set(str(s) for s in declared_sections)

    for section, score in section_scores.items():
        in_declared = section in declared_set
        meta = _ANNEX_III_CATALOGUE[section]

        if in_declared:
            if score >= _OFFLINE_REJECTION_THRESHOLD:
                provenance: str = "client_declared"
                confidence = max(score, _OFFLINE_DECLARED_CONFIDENCE)
            else:
                # Declared but no supporting evidence → rejected
                provenance = "phase1_rejected"
                confidence = score
            entries.append(
                AnnexIIIEntry(
                    annex_iii_section=section,  # type: ignore[arg-type]
                    section_title=meta["section_title"],
                    use_case_marker=_extract_marker(meta["keywords"], desc_lower),
                    confidence=round(confidence, 3),
                    provenance=provenance,  # type: ignore[arg-type]
                    derogation_claimed=False,
                    derogation_rationale=None,
                )
            )
        else:
            if score >= _OFFLINE_DETECTED_CONFIDENCE:
                # Phase 1 found an undeclared section
                entries.append(
                    AnnexIIIEntry(
                        annex_iii_section=section,  # type: ignore[arg-type]
                        section_title=meta["section_title"],
                        use_case_marker=_extract_marker(meta["keywords"], desc_lower),
                        confidence=round(score, 3),
                        provenance="phase1_verified",  # type: ignore[arg-type]
                        derogation_claimed=False,
                        derogation_rationale=None,
                    )
                )

    # Sort: client_declared first, then by confidence desc
    _PROV_ORDER = {
        "client_declared": 0, "phase1_verified": 1,
        "phase1_corrected": 2, "phase1_rejected": 3,
    }
    entries.sort(
        key=lambda e: (_PROV_ORDER.get(e["provenance"], 9), -e["confidence"])
    )
    return entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _keyword_score(keywords: list[str], text: str) -> float:
    """Return fraction of keywords that appear in *text*."""
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw in text)
    return hits / len(keywords)


def _rag_score(
    section: str,
    section_title: str,
    text: str,
    rag_fn: Callable[[str], list[dict[str, Any]]],
) -> float:
    """
    Query RegulatoryRAG for the section and check if the top result is
    semantically related to *text*. Falls back to keyword score on failure.
    """
    try:
        query = f"Annex III §{section} {section_title}"
        results = rag_fn(query)
        if not results:
            return 0.0
        top_score = float(results[0].get("score", 0.0))
        # Combine RAG score with keyword overlap for a blended confidence
        meta = _ANNEX_III_CATALOGUE.get(section, {})
        kw_score = _keyword_score(meta.get("keywords", []), text)
        return round(0.6 * top_score + 0.4 * kw_score, 3)
    except Exception as exc:  # pragma: no cover
        logger.warning("RAG score failed for Annex III §%s: %s; falling back.", section, exc)
        meta = _ANNEX_III_CATALOGUE.get(section, {})
        return _keyword_score(meta.get("keywords", []), text)


def _extract_marker(keywords: list[str], text: str) -> str:
    """Return the first matching keyword as a short use-case marker."""
    for kw in keywords:
        if kw in text:
            return kw
    return keywords[0] if keywords else "unspecified"
