"""
pii_scan — PII entity detection wrapper (§4.1).

Returns a structured dict compatible with T07_data_quality_report ``pii_scan``
block and T08_special_category_data_log.

Production path:  Microsoft Presidio ``AnalyzerEngine``.
Offline/fallback: keyword-regex heuristic over column names.

The function also returns a ``special_category_data_detected`` flag which
Phase 2 DataAuditor propagates back to ``AuditState.special_category_data``.

Usage
-----
    from src.tools.pii_scan import pii_scan

    result = pii_scan(df, language="en")
    if result["special_category_data_detected"]:
        state["special_category_data"] = True
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Presidio entity → GDPR Art. 9 special-category mapping
# ---------------------------------------------------------------------------
_SPECIAL_CATEGORY_ENTITIES: dict[str, str] = {
    "MEDICAL_LICENSE": "health_data",
    "US_ITIN": "health_data",          # often tied to health insurance
    "NRP": "racial_or_ethnic_origin",  # National Registration Person
    "POLITICAL_OPINION": "political_opinions",
    "TRADE_UNION_MEMBERSHIP": "trade_union_membership",
    "GENETIC": "genetic_data",
    "BIOMETRIC": "biometric_data",
    "HEALTH": "health_data",
    "RELIGION": "religious_beliefs",
    "SEXUAL_ORIENTATION": "sex_life_or_orientation",
    "CRIMINAL": "criminal_convictions",
    "RACE": "racial_or_ethnic_origin",
    "ETHNIC_GROUP": "racial_or_ethnic_origin",
}

_HIGH_SEVERITY_ENTITIES = {
    "MEDICAL_LICENSE", "NRP", "BIOMETRIC", "HEALTH", "GENETIC",
    "POLITICAL_OPINION", "CRIMINAL", "RACE", "ETHNIC_GROUP",
    "SEXUAL_ORIENTATION", "TRADE_UNION_MEMBERSHIP",
}

# ---------------------------------------------------------------------------
# Column-name keyword heuristic for offline fallback
# ---------------------------------------------------------------------------
_KEYWORD_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, entity_type, severity)
    (r"health|diagnosis|disease|medication|prescription", "HEALTH", "high"),
    (r"race|ethnic|national.?origin", "RACE", "high"),
    (r"biometric|fingerprint|iris|retina|face.?id", "BIOMETRIC", "critical"),
    (r"religion|faith|church|mosque|synagogue", "RELIGION", "high"),
    (r"politic|party|vote|union|union.?member", "POLITICAL_OPINION", "high"),
    (r"sex.?orient|gender.?ident|lgbtq", "SEXUAL_ORIENTATION", "high"),
    (r"criminal|conviction|arrest|offence", "CRIMINAL", "high"),
    (r"genetic|dna|genome", "GENETIC", "critical"),
    (r"email|e.?mail", "EMAIL_ADDRESS", "medium"),
    (r"phone|mobile|tel", "PHONE_NUMBER", "medium"),
    (r"ssn|social.?security|national.?id|passport|id.?number", "US_SSN", "high"),
    (r"credit.?card|card.?number|cvv", "CREDIT_CARD", "high"),
    (r"address|street|postcode|zip.?code", "LOCATION", "low"),
    (r"name|first.?name|last.?name|surname", "PERSON", "low"),
    (r"ip.?address|ipv4|ipv6", "IP_ADDRESS", "medium"),
]


def pii_scan(
    df: Any,
    language: str = "en",
    sample_rows: int = 200,
) -> dict[str, Any]:
    """
    Scan a DataFrame for PII and special-category personal data.

    Parameters
    ----------
    df:
        A ``pandas.DataFrame``.
    language:
        Language code for Presidio AnalyzerEngine (default ``"en"``).
    sample_rows:
        Maximum number of rows to sample for text-based analysis (default 200).

    Returns
    -------
    dict matching the T07 ``pii_scan`` sub-schema:
        {
            pii_detected, entities_found, special_category_data_detected,
            special_categories_found, analyser_engine, language
        }
    """
    try:
        return _scan_presidio(df, language, sample_rows)
    except Exception as exc:
        logger.info("Presidio unavailable (%s); using keyword heuristic.", exc)
        return _scan_keyword(df, language)


# ---------------------------------------------------------------------------
# Presidio path
# ---------------------------------------------------------------------------

def _scan_presidio(df: Any, language: str, sample_rows: int) -> dict[str, Any]:
    """Use Microsoft Presidio for entity recognition."""
    from presidio_analyzer import AnalyzerEngine  # type: ignore  # pragma: no cover

    engine = AnalyzerEngine()  # pragma: no cover
    entities_found: list[dict[str, Any]] = []  # pragma: no cover
    special_categories: set[str] = set()  # pragma: no cover

    sample = df.head(sample_rows)  # pragma: no cover
    for col in sample.columns:  # pragma: no cover
        col_str = str(col)  # pragma: no cover
        # Concatenate sample values to a single text blob for analysis
        try:  # pragma: no cover
            text_blob = " ".join(str(v) for v in sample[col].dropna().astype(str).tolist())  # pragma: no cover
        except Exception:  # pragma: no cover
            continue  # pragma: no cover

        if not text_blob.strip():  # pragma: no cover
            continue  # pragma: no cover

        results = engine.analyze(text=text_blob[:10_000], language=language)  # pragma: no cover
        entity_counts: dict[str, int] = {}  # pragma: no cover
        for r in results:  # pragma: no cover
            entity_counts[r.entity_type] = entity_counts.get(r.entity_type, 0) + 1  # pragma: no cover

        for etype, cnt in entity_counts.items():  # pragma: no cover
            severity = "high" if etype in _HIGH_SEVERITY_ENTITIES else "medium"  # pragma: no cover
            entities_found.append(  # pragma: no cover
                {
                    "entity_type": etype,
                    "column_name": col_str,
                    "sample_count": cnt,
                    "severity": severity,
                }
            )
            if etype in _SPECIAL_CATEGORY_ENTITIES:  # pragma: no cover
                special_categories.add(_SPECIAL_CATEGORY_ENTITIES[etype])  # pragma: no cover

    return {  # pragma: no cover
        "pii_detected": len(entities_found) > 0,
        "entities_found": entities_found,
        "special_category_data_detected": len(special_categories) > 0,
        "special_categories_found": sorted(special_categories),
        "analyser_engine": "presidio",
        "language": language,
    }


# ---------------------------------------------------------------------------
# Keyword-heuristic fallback
# ---------------------------------------------------------------------------

def _scan_keyword(df: Any, language: str) -> dict[str, Any]:
    """Column-name keyword heuristic — no external dependencies."""
    entities_found: list[dict[str, Any]] = []
    special_categories: set[str] = set()

    try:
        columns = list(df.columns)
    except Exception:
        columns = []

    for col in columns:
        col_lower = str(col).lower().replace("_", " ").replace("-", " ")
        for pattern, etype, severity in _KEYWORD_PATTERNS:
            if re.search(pattern, col_lower):
                entities_found.append(
                    {
                        "entity_type": etype,
                        "column_name": str(col),
                        "sample_count": 1,  # conservative — 1 per column
                        "severity": severity,
                    }
                )
                if etype in _SPECIAL_CATEGORY_ENTITIES:
                    special_categories.add(_SPECIAL_CATEGORY_ENTITIES[etype])
                break  # one match per column is enough

    return {
        "pii_detected": len(entities_found) > 0,
        "entities_found": entities_found,
        "special_category_data_detected": len(special_categories) > 0,
        "special_categories_found": sorted(special_categories),
        "analyser_engine": "keyword-heuristic",
        "language": language,
    }
