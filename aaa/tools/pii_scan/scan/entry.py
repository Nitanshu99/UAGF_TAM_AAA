"""The ``pii_scan`` entry point: Presidio over the values, else the column-name heuristic."""
from __future__ import annotations

from typing import Any

from aaa.tools.pii_scan.logger import logger
from aaa.tools.pii_scan.scan.keyword import _scan_keyword
from aaa.tools.pii_scan.scan.presidio import _scan_presidio


def _not_scanned(language: str) -> dict[str, Any]:
    """No values were examined: detection is unknown (null), not "none found"."""
    return {"pii_detected": None, "entities_found": [],
            "special_category_data_detected": None, "special_categories_found": [],
            "unresolved_mentions": [], "analyser_engine": None, "language": language}


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
            special_categories_found, unresolved_mentions, analyser_engine, language
        }
    """
    if df is None or len(df) == 0:
        return _not_scanned(language)
    try:
        return _scan_presidio(df, language, sample_rows)
    except Exception as exc:
        logger.info("Presidio unavailable (%s); using keyword heuristic.", exc)
        return _scan_keyword(df, language)
