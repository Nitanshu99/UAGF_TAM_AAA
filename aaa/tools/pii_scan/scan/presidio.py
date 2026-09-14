"""Microsoft Presidio entity recognition over a sampled frame, one cell at a time.

See :mod:`aaa.tools.pii_scan.scan.aggregate` for why cells are analysed separately
and what labels a column. The output shape is unchanged: T07's
``pii_scan.entities_found[]`` items allow no new keys, so ``sample_count`` is the
number of sampled cells carrying the entity.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from aaa.tools.pii_scan.logger import (
    _HIGH_SEVERITY_ENTITIES,
    _SPECIAL_CATEGORY_ENTITIES,
    MIN_ENTITY_SCORE,
)
from aaa.tools.pii_scan.scan.aggregate import column_entities, language_results, unresolved_mention
from aaa.tools.pii_scan.scan.frame import _column_cells, _is_numeric, _sample


@lru_cache(maxsize=1)
def _analyzer() -> Any:  # pragma: no cover - needs presidio and a spaCy model
    """One AnalyzerEngine per process: building one loads the spaCy model."""
    from presidio_analyzer import AnalyzerEngine  # type: ignore

    return AnalyzerEngine()


def _scan_presidio(df: Any, language: str, sample_rows: int) -> dict[str, Any]:  # pragma: no cover
    """Use Microsoft Presidio for entity recognition, per cell."""
    from presidio_analyzer import BatchAnalyzerEngine  # type: ignore

    batch = BatchAnalyzerEngine(analyzer_engine=_analyzer())
    sample = _sample(df, sample_rows)
    entities_found: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    special_categories: set[str] = set()
    for col in sample.columns:
        cells = _column_cells(sample, col)
        if not cells:
            continue
        numeric = _is_numeric(sample[col])
        results = [language_results(cell, list(r), numeric) for cell, r in zip(
            cells, batch.analyze_iterator(cells, language=language,
                                          score_threshold=MIN_ENTITY_SCORE))]
        for etype, count in column_entities(results, len(cells)).items():
            entities_found.append({"entity_type": etype, "column_name": str(col),
                                   "sample_count": count,
                                   "severity": "high" if etype in _HIGH_SEVERITY_ENTITIES
                                   else "medium"})
            if etype in _SPECIAL_CATEGORY_ENTITIES:
                special_categories.add(_SPECIAL_CATEGORY_ENTITIES[etype])
            mention = unresolved_mention(str(col), etype, count, cells, results)
            unresolved += [mention] if mention else []
    return {"pii_detected": bool(entities_found), "entities_found": entities_found,
            "special_category_data_detected": bool(special_categories),
            "special_categories_found": sorted(special_categories),
            "unresolved_mentions": unresolved,
            "analyser_engine": "presidio", "language": language}


__all__ = ["_sample", "_scan_presidio"]
