"""pii_scan — PII entity detection wrapper (§4.1).

Returns a structured dict compatible with T07_data_quality_report ``pii_scan``
block and T08_special_category_data_log.

Production path:  Microsoft Presidio ``AnalyzerEngine``.
Fallback: keyword-regex heuristic over column names (a match is an observation;
          no match leaves detection null).

The function also returns a ``special_category_data_detected`` flag which
Phase 2 DataAuditor propagates back to ``AuditState.special_category_data``.

Usage
-----
    from src.tools.pii_scan import pii_scan

    result = pii_scan(df, language="en")
    if result["special_category_data_detected"]:
        state["special_category_data"] = True"""
from aaa.tools.pii_scan.logger import (  # noqa: F401
    _HIGH_SEVERITY_ENTITIES,
    _KEYWORD_PATTERNS,
    _SPECIAL_CATEGORY_ENTITIES,
    logger,
)
from aaa.tools.pii_scan.scan.entry import pii_scan  # noqa: F401
from aaa.tools.pii_scan.scan.keyword import _scan_keyword  # noqa: F401
from aaa.tools.pii_scan.scan.presidio import _scan_presidio  # noqa: F401

__all__ = [
    'logger',
    '_SPECIAL_CATEGORY_ENTITIES',
    '_HIGH_SEVERITY_ENTITIES',
    '_KEYWORD_PATTERNS',
    '_scan_presidio',
    '_scan_keyword',
    'pii_scan',
]
