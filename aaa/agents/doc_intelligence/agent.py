"""The DocIntelligenceAgent class — pre-intake field extraction coordinator."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.base import BaseAgent
from aaa.agents.doc_intelligence.contexts import gather_field_contexts
from aaa.agents.doc_intelligence.llm import extract_fields
from aaa.agents.doc_intelligence.parse import build_result
from aaa.agents.doc_intelligence.queries import empty_result
from aaa.platform.evidence import EvidenceStore
from aaa.platform.state import DocExtractionResult

logger = logging.getLogger(__name__)


class DocIntelligenceAgent(BaseAgent):
    """Pre-intake document intelligence agent.

    Ingests customer-uploaded artefacts and extracts Stage A / Stage B triage
    fields so the wizard UI can pre-populate the review form.  Uses gpt-5.6-terra
    on the default (non-Flex) tier — interactive critical path.
    """

    def __init__(self, evidence_store: EvidenceStore):
        from aaa.platform.model_registry import get_model_config
        cfg = get_model_config("DocIntelligenceAgent")
        super().__init__(name="DocIntelligenceAgent", model=cfg.model,
                         service_tier=cfg.service_tier)
        self.store = evidence_store

    async def process(self, message: dict[str, Any]) -> DocExtractionResult:  # type: ignore[override]
        """Extract Stage A/B fields from uploaded documents.

        :param message: ``engagement_id`` (str) and ``doc_uris`` (list[str]) —
            URIs already stored in the EvidenceStore from the upload step.
        :returns: Pre-filled field values with confidence scores and source
            attribution; an empty result when no documents are provided.
        """
        engagement_id: str = message["engagement_id"]
        doc_uris: list[str] = message.get("doc_uris", [])
        if not doc_uris:
            logger.info("[DocIntelligenceAgent] no documents provided — "
                        "returning empty result.")
            return empty_result("no_documents")

        from aaa.tools.client_doc_ingest import client_doc_ingest
        ingest_result = client_doc_ingest(engagement_id, doc_uris, self.store)
        logger.info("[DocIntelligenceAgent] Ingested %d chunks from %d sources.",
                    ingest_result.get("chunks_indexed", 0),
                    len(ingest_result.get("sources", [])))
        if ingest_result.get("chunks_indexed", 0) == 0:
            logger.warning("[DocIntelligenceAgent] %d document(s) uploaded but nothing "
                           "was indexed; the form cannot be pre-filled.", len(doc_uris))
            return empty_result("not_indexed")

        field_contexts = gather_field_contexts(engagement_id)
        if not field_contexts:
            logger.warning("[DocIntelligenceAgent] retrieval matched no field context "
                           "in %d indexed chunk(s).", ingest_result.get("chunks_indexed", 0))
            return empty_result("no_context")
        llm_output = await extract_fields(self, field_contexts)
        if llm_output is None:
            return empty_result("llm_failed")
        return build_result(llm_output, field_contexts)
