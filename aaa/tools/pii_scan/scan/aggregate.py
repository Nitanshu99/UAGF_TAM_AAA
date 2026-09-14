"""Per-column aggregation of per-cell Presidio results — pure, so it is testable without spaCy.

The scan used to join each column's first values into one string and analyse
that. spaCy then read ``"JOB-0026 JOB-0028"`` as a nationality/religious/political
group, and case 06's T08 logged racial-or-ethnic-origin data the provider had
correctly declared absent (T-20260913-012). Presidio's own tabular builder
(``presidio_structured``) analyses each value separately; a column is labelled
only when enough of its cells carry the entity.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable

from aaa.tools.pii_scan.logger import _UNRESOLVED_ENTITIES, MIN_COLUMN_RATE, MIN_ENTITY_SCORE

#: How many of an unresolved entity's most frequent matched terms are recorded.
MATCHED_TERMS_KEPT = 5

#: Presidio's named-entity-model recognizers: they read language, nothing else.
NER_RECOGNIZERS = frozenset({"SpacyRecognizer", "StanzaRecognizer", "TransformersRecognizer"})
#: A value with no letters, or one whitespace-free token joined by underscores.
_NOT_LANGUAGE = re.compile(r"^[^A-Za-z]*$|^\S*_\S*$")


def language_results(cell: str, results: list[Any], numeric: bool) -> list[Any]:
    """Drop named-entity results on a value that is not language.

    Case 01's scan read the integers of ``credit_amount`` ("5823") as DATE_TIME and
    the code ``radio_tv`` as a PERSON — spaCy's entity model applied to a number and
    an identifier (T-20260913-108). Pattern recognizers (card, phone, IBAN) still
    apply to such values; only the language model's guesses are removed.

    :param cell: The analysed value, as text.
    :param results: Presidio results for it.
    :param numeric: The column holds numbers.
    :returns: The results that read language, or that no language model produced.
    """
    if not (numeric or _NOT_LANGUAGE.match(cell.strip())):
        return results
    return [r for r in results if (getattr(r, "recognition_metadata", None) or {}).get(
        "recognizer_name") not in NER_RECOGNIZERS]


def column_entities(cell_results: Iterable[Iterable[Any]], sampled_cells: int,
                    min_rate: float = MIN_COLUMN_RATE,
                    min_score: float = MIN_ENTITY_SCORE) -> dict[str, int]:
    """Entity types present in enough of a column's cells.

    :param cell_results: One iterable of Presidio results per analysed cell.
    :param sampled_cells: Non-empty cells analysed, the rate's denominator.
    :param min_rate: Share of cells an entity must reach to label the column.
    :param min_score: Confidence below which a result is ignored.
    :returns: ``{entity_type: cells containing it}``, for types at or above the rate.
    """
    counts: Counter[str] = Counter()
    for results in cell_results:
        counts.update({str(r.entity_type) for r in results
                       if float(getattr(r, "score", 1.0)) >= min_score})
    if sampled_cells <= 0:
        return {}
    return {etype: cells for etype, cells in counts.items() if cells / sampled_cells >= min_rate}


def matched_terms(cells: list[str], cell_results: list[list[Any]], entity_type: str,
                  min_score: float = MIN_ENTITY_SCORE) -> list[str]:
    """The entity's most frequent matched spans, lower-cased, most frequent first.

    :param cells: The analysed cell texts.
    :param cell_results: Presidio results per cell, aligned with *cells*.
    :param entity_type: The entity whose spans are wanted.
    :param min_score: Confidence below which a result is ignored.
    :returns: Up to :data:`MATCHED_TERMS_KEPT` distinct terms.
    """
    terms: Counter[str] = Counter()
    for text, results in zip(cells, cell_results):
        terms.update(text[r.start:r.end].strip().lower() for r in results
                     if str(r.entity_type) == entity_type
                     and float(getattr(r, "score", 1.0)) >= min_score)
    return [term for term, _ in terms.most_common(MATCHED_TERMS_KEPT) if term]


def unresolved_mention(column: str, entity_type: str, count: int, cells: list[str],
                       cell_results: list[list[Any]]) -> dict[str, Any] | None:
    """A ``pii_scan.unresolved_mentions`` item, or ``None`` for an entity that resolves.

    :param column: Column name.
    :param entity_type: Detected entity type.
    :param count: Sampled cells carrying it.
    :param cells: The analysed cell texts.
    :param cell_results: Presidio results per cell, aligned with *cells*.
    :returns: Entity, column, cell count, matched terms and why no category is recorded.
    """
    if entity_type not in _UNRESOLVED_ENTITIES:
        return None
    return {"entity_type": entity_type, "column_name": column, "sample_count": count,
            "matched_terms": matched_terms(cells, cell_results, entity_type),
            "reason": _UNRESOLVED_ENTITIES[entity_type]}


__all__ = ["NER_RECOGNIZERS", "column_entities", "language_results", "matched_terms",
           "unresolved_mention"]
