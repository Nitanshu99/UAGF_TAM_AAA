"""Column-name keyword heuristic used when Presidio cannot run."""
from __future__ import annotations

import re
from typing import Any

from aaa.tools.pii_scan.logger import (  # noqa: F401
    _HIGH_SEVERITY_ENTITIES,
    _KEYWORD_PATTERNS,
    _SPECIAL_CATEGORY_ENTITIES,
    logger,
)


def _scan_keyword(df: Any, language: str) -> dict[str, Any]:
    """Column-name keyword heuristic — no external dependencies.

    It reads column *names*, never values, so a match is an observation while no
    match proves nothing: detection is then null, and no cell count is claimed
    (``sample_count`` was once hard-coded to 1, T-20260913-062).
    """
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
                        "sample_count": None,  # names were read, not cells
                        "severity": severity,
                    }
                )
                if etype in _SPECIAL_CATEGORY_ENTITIES:
                    special_categories.add(_SPECIAL_CATEGORY_ENTITIES[etype])
                break  # one match per column is enough

    return {
        "pii_detected": True if entities_found else None,
        "entities_found": entities_found,
        "special_category_data_detected": True if special_categories else None,
        "special_categories_found": sorted(special_categories),
        "unresolved_mentions": [],  # names carry no matched spans to resolve
        "analyser_engine": "keyword-heuristic",
        "language": language,
    }
