"""Combined field-query map and the empty extraction result."""
from __future__ import annotations

from aaa.agents.doc_intelligence.queries.stage.a import STAGE_A_FIELDS, STAGE_A_QUERIES
from aaa.agents.doc_intelligence.queries.stage.b import STAGE_B_QUERIES
from aaa.platform.state import DocExtractionResult

#: All extractable fields (Stage A + Stage B) keyed to their search queries.
FIELD_QUERIES: dict[str, str] = {**STAGE_A_QUERIES, **STAGE_B_QUERIES}

__all__ = ["FIELD_QUERIES", "STAGE_A_FIELDS", "empty_result"]


def empty_result(status: str = "no_documents") -> DocExtractionResult:
    """Return the all-fields-missing extraction result.

    Five different failures used to land here indistinguishably, and the wizard
    rendered all of them as "Not found in uploaded documents — please fill in
    manually" (M23). Only ``no_documents`` means that. The others mean the
    agent never got to look, and telling a customer their dossier is missing
    information the system failed to read is the wrong answer to give them.

    :param status: Why the result is empty — ``no_documents``, ``not_indexed``,
        ``no_context``, ``llm_failed`` or ``unparsable_reply``.
    :returns: A :class:`DocExtractionResult` with every field reported missing.
    """
    return {
        "stage_a_partial": {},
        "stage_b_partial": {},
        "field_confidence": {},
        "field_sources": {},
        "missing_fields": list(FIELD_QUERIES.keys()),
        "extraction_status": status,
    }
