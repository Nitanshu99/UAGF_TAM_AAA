"""Pipeline wrappers used by the wizard steps."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aaa.agents.base import IntakeDispatch
from aaa.agents.intake_validator import IntakeValidator
from aaa.agents.tier1.orchestrator import Orchestrator
from aaa.agents.tier1.regulatory_rag import build_regulatory_rag
from aaa.platform.evidence import EvidenceStore

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


def ingest_documents(engagement_id: str, doc_uris: list[str], store: EvidenceStore) -> dict:
    """Index the customer's uploads into this engagement's document collection.

    This used to be :class:`DocIntelligenceAgent`, which did two things: indexed
    the documents, then spent an LLM call reading Stage A/B field values out of
    them to pre-fill the review form. Only the first is load-bearing. The audit
    runs on what the customer confirms in the form, and the *collection* built
    here is what phases 1–5 and the scope / data / model / governance agents
    actually retrieve against — ``IntakeValidator`` only indexes the seven named
    Stage B URI fields, so free-form technical documentation reaches the audit
    through this call and no other.

    Dropping the extraction half takes the one interactive-critical-path LLM
    call out of the wizard. The agent and its ``/extract-triage`` endpoint are
    untouched for callers that still want pre-fill.

    ``client_doc_ingest`` resets the collection once per run, not once per call,
    so this and the IntakeValidator's later ingest both contribute to it.

    :param engagement_id: Engagement identifier.
    :param doc_uris: Evidence-store URIs of the uploaded documents.
    :param store: Evidence store holding the documents.
    :returns: ``{collection_name, chunks_indexed, sources}``; a failed ingest is
        reported, not raised — a customer can still complete the form by hand.
    """
    from aaa.tools.client_doc_ingest import ClientDocIngestError, client_doc_ingest
    if not doc_uris:
        return {"chunks_indexed": 0, "sources": [], "error": None}
    try:
        result = dict(client_doc_ingest(engagement_id, doc_uris, store))
    except ClientDocIngestError as exc:
        logger.warning("client_doc_ingest failed for %s: %s", engagement_id, exc)
        return {"chunks_indexed": 0, "sources": [], "error": str(exc)}
    result["error"] = None
    return result


async def run_pipeline(
    engagement_id: str, stage_a: dict, stage_b: dict, stage_c: dict | None, store: EvidenceStore,
) -> dict:
    """Run IntakeValidator → Orchestrator and return the final AuditState.

    :param engagement_id: Engagement identifier.
    :param stage_a: Stage A declaration payload.
    :param stage_b: Stage B technical documentation payload.
    :param stage_c: Optional Stage C scoped-access payload.
    :param store: Evidence store for artefact persistence.
    :returns: Final ``AuditState`` dictionary.
    """
    stage_a_uri = store.store_artefact(engagement_id, "stage_a_raw", "stage_a_raw", stage_a, "streamlit")
    stage_b_uri = store.store_artefact(engagement_id, "stage_b_raw", "stage_b_raw", stage_b, "streamlit")
    stage_c_uri = (
        store.store_artefact(engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "streamlit")
        if stage_c is not None else None
    )
    dispatch: IntakeDispatch = {
        "engagement_id": engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }
    initial = await IntakeValidator(evidence_store=store).process(dispatch)
    return await Orchestrator(evidence_store=store,
                              regulatory_rag=build_regulatory_rag(),
                              ).run(dict(initial))
