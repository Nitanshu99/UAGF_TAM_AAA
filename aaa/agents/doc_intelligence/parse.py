"""Translation of the LLM extraction output into a DocExtractionResult."""
from __future__ import annotations

from typing import Any

from aaa.agents.doc_intelligence.queries import FIELD_QUERIES, STAGE_A_FIELDS
from aaa.platform.state import DocExtractionResult

#: Values below this confidence are treated as not found.
CONFIDENCE_FLOOR = 0.35

#: Share of the asked-for fields a reply must yield to count as a reading of
#: the documents rather than a mangled one. Deliberately low: a dossier really
#: can be missing most of Annex IV, and that is a finding worth showing.
_MIN_YIELD = 0.10


def build_result(
    llm_output: dict[str, Any],
    field_contexts: dict[str, dict[str, Any]],
) -> DocExtractionResult:
    """Build the extraction result from the batched LLM output.

    :param llm_output: Field → ``{value, confidence}`` mapping from the LLM.
    :param field_contexts: Field → retrieval context (for source attribution).
    :returns: Populated :class:`DocExtractionResult` with low-confidence and
        absent fields listed under ``missing_fields``.
    """
    stage_a_partial: dict[str, Any] = {}
    stage_b_partial: dict[str, Any] = {}
    field_confidence: dict[str, float] = {}
    field_sources: dict[str, str] = {}
    missing: list[str] = []
    for field in FIELD_QUERIES:
        entry = llm_output.get(field, {})
        if not isinstance(entry, dict):
            missing.append(field)
            continue
        value = entry.get("value")
        confidence = float(entry.get("confidence", 0.0))
        if value is None or confidence < CONFIDENCE_FLOOR:
            missing.append(field)
            continue
        target = stage_a_partial if field in STAGE_A_FIELDS else stage_b_partial
        target[field] = value
        field_confidence[field] = confidence
        field_sources[field] = field_contexts.get(field, {}).get("best_source", "document")
    return {
        "stage_a_partial": stage_a_partial,
        "stage_b_partial": stage_b_partial,
        "field_confidence": field_confidence,
        "field_sources": field_sources,
        "missing_fields": missing,
        "extraction_status": _status(field_confidence, field_contexts),
    }


def _status(extracted: dict[str, float], field_contexts: dict[str, dict[str, Any]]) -> str:
    """Say whether this reply is a reading of the documents or the wreck of one.

    A reply can be valid JSON and still carry almost nothing. On the
    2026-09-10 UI run the model mis-escaped the very first value —
    ``{"provider_name":{"value\":\"Mariposa-Edu GmbH…`` — and every one of the
    9,327 characters it had correctly extracted ended up nested inside
    ``provider_name`` as malformed sub-keys. One field of twenty survived, the
    wizard reported "Not found in uploaded documents" against the other
    nineteen, and intake completeness read 0 % on a dossier that contained
    every answer (M23).

    Retrieval already decided these fields were worth asking about — a context
    was found for each — so recovering almost none of them is a parse failure,
    not a set of absent facts.

    :param extracted: Fields that survived with usable confidence.
    :param field_contexts: Fields retrieval found any context for.
    :returns: ``ok`` or ``unparsable_reply``.
    """
    asked = len(field_contexts)
    if not asked:
        return "ok"
    return "ok" if len(extracted) > max(1, asked * _MIN_YIELD) else "unparsable_reply"
