"""
DocIntelligenceAgent — pre-intake document extraction agent (§6 Stage 0 extension).

Reads all customer-uploaded artefacts from an engagement's EvidenceStore (already
ingested into the per-engagement Qdrant collection) and extracts every Stage A / Stage
B field it can find, returning a :class:`DocExtractionResult` that the wizard UI uses
to pre-populate the review form.

Model: gpt-5.4 on the **default (non-Flex) tier** — this agent is on the interactive
critical path (user waits for it) and must not risk a 429 from spare-capacity
exhaustion that Flex processing can surface at peak load.

Offline mode: returns an empty result immediately (no Qdrant / OpenAI credentials
needed) so the wizard still works without infrastructure.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from aaa.agents.base import BaseAgent
from aaa.platform.evidence import EvidenceStore
from aaa.platform.state import DocExtractionResult

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Field extraction query map  (field_name → plain-English search query)
# ---------------------------------------------------------------------------

_STAGE_A_FIELDS: frozenset[str] = frozenset({
    "provider_name", "system_name", "version",
    "intended_purpose", "declared_modality", "declared_risk_tier",
})

# Queries are used both to search the Qdrant collection and as field descriptions
# in the batched LLM prompt.
_FIELD_QUERIES: dict[str, str] = {
    # Stage A
    "provider_name": (
        "What is the full legal name of the organisation or company that developed, "
        "trained, or places this AI system on the market?"
    ),
    "system_name": "What is the commercial or internal name / title of this AI system?",
    "version": "What is the version number of this AI system? e.g. 1.0, 2.3.1",
    "intended_purpose": (
        "What is the intended purpose, use case, or task that this AI system is "
        "designed to perform? Who uses it and in what context?"
    ),
    "declared_modality": (
        "What type of AI model or machine learning approach is used? "
        "Options: tabular (structured ML), cv (computer vision), nlp (text/language), "
        "time_series, llm (large language model), agentic (autonomous agent), gpai (foundation model)."
    ),
    "declared_risk_tier": (
        "Is this AI system classified as high-risk, limited risk, minimal risk, or "
        "general-purpose AI (gpai) under the EU AI Act?"
    ),
    # Stage B — Annex IV §1–§9
    "general_description": (
        "Provide a general description of this AI system: its overall purpose, "
        "the problem it solves, who is responsible for it, and who the end users are."
    ),
    "model_type": (
        "What is the technical architecture or model type? "
        "e.g. XGBoost classifier v1.2, BERT fine-tune, GPT-4 fine-tune, ResNet-50."
    ),
    "design_process": (
        "How was this model designed and developed? Describe the training methodology, "
        "architecture choices, key design decisions, and iterations."
    ),
    "training_data_description": (
        "What training and validation datasets were used? Include source, size, "
        "date range, and how the data was collected or curated."
    ),
    "data_governance_measures": (
        "What data governance, quality controls, access control, or data management "
        "practices are in place? e.g. anonymisation, consent, bias review."
    ),
    "monitoring_measures": (
        "How is the system monitored after deployment? What oversight mechanisms, "
        "drift detection, or human-in-the-loop triggers exist?"
    ),
    "logging_capabilities": (
        "What logging and audit trail capabilities does the system have? "
        "What events are recorded and what is the retention period?"
    ),
    "accuracy_metrics": (
        "What performance metrics are reported for this system? "
        "e.g. accuracy, AUC, F1 score, precision, recall, RMSE."
    ),
    "lifecycle_change_log": (
        "What significant changes or updates have been made to the system since "
        "initial deployment or the last version?"
    ),
    "harmonised_standards": (
        "What ISO, IEC, or EU harmonised standards has this system been developed "
        "in accordance with? e.g. ISO/IEC 42001:2023, ISO/IEC 23894:2023."
    ),
}

_SYSTEM_PROMPT = (
    "You are a compliance documentation analyst specialised in the EU AI Act.\n"
    "You extract specific compliance form fields from AI system documentation.\n\n"
    "Given retrieved document chunks for each field, extract the value if clearly present.\n"
    "Return a single JSON object where each key is a field name and each value is:\n"
    "  {\"value\": <extracted string or null if not found>, \"confidence\": <0.0-1.0>}\n\n"
    "Rules:\n"
    "- Be conservative: if information is not clearly stated, return null rather than guessing.\n"
    "- For accuracy_metrics, return a JSON string like '{\"accuracy\": 0.78, \"f1\": 0.71}'.\n"
    "- For lifecycle_change_log, return a newline-separated string of changes.\n"
    "- For harmonised_standards, return a comma-separated string of standards.\n"
    "- confidence >= 0.7 means the text clearly states this; 0.4–0.7 means inferred; < 0.4 is uncertain."
)


def _empty_result() -> DocExtractionResult:
    return {
        "stage_a_partial": {},
        "stage_b_partial": {},
        "field_confidence": {},
        "field_sources": {},
        "missing_fields": list(_FIELD_QUERIES.keys()),
    }


class DocIntelligenceAgent(BaseAgent):
    """
    Pre-intake document intelligence agent.

    Ingests customer-uploaded artefacts and extracts Stage A / Stage B triage fields
    so the wizard UI can pre-populate the review form. Uses gpt-5.4 on the default
    (non-Flex) tier — interactive critical path.
    """

    def __init__(self, evidence_store: EvidenceStore):
        from aaa.platform.model_registry import get_model_config
        cfg = get_model_config("DocIntelligenceAgent")
        super().__init__(name="DocIntelligenceAgent", model=cfg.model, service_tier=cfg.service_tier)
        self.store = evidence_store

    async def process(self, message: dict[str, Any]) -> DocExtractionResult:  # type: ignore[override]
        """
        Extract Stage A/B fields from uploaded documents.

        Parameters
        ----------
        message : dict
            ``engagement_id`` (str) and ``doc_uris`` (list[str]) — URIs already
            stored in the EvidenceStore from the upload step.

        Returns
        -------
        DocExtractionResult
            Pre-filled field values with confidence scores and source attribution.
            Returns an empty result when offline or when no documents are provided.
        """
        engagement_id: str = message["engagement_id"]
        doc_uris: list[str] = message.get("doc_uris", [])

        if _OFFLINE or not doc_uris:
            logger.info(
                "[DocIntelligenceAgent] offline=%s, doc_uris=%d — returning empty result.",
                _OFFLINE, len(doc_uris),
            )
            return _empty_result()

        # 1. Ingest documents into per-engagement Qdrant collection.
        from aaa.tools.client_doc_ingest import client_doc_ingest, client_doc_search
        ingest_result = client_doc_ingest(engagement_id, doc_uris, self.store)
        logger.info(
            "[DocIntelligenceAgent] Ingested %d chunks from %d sources.",
            ingest_result.get("chunks_indexed", 0),
            len(ingest_result.get("sources", [])),
        )

        if ingest_result.get("chunks_indexed", 0) == 0:
            return _empty_result()

        # 2. Search for each field and collect contexts.
        field_contexts: dict[str, dict] = {}
        for field, query in _FIELD_QUERIES.items():
            hits = client_doc_search(engagement_id, query, top_k=3)
            if hits:
                field_contexts[field] = {
                    "context": "\n\n".join(h["text"] for h in hits[:3]),
                    "best_source": (
                        f"{hits[0].get('source_uri', 'doc')} p.{hits[0].get('page_number', '?')}"
                    ),
                    "best_score": float(hits[0].get("score", 0.0)),
                }

        if not field_contexts:
            return _empty_result()

        # 3. Single batched LLM call to extract all fields.
        user_payload = {
            "task": "Extract EU AI Act compliance form fields from retrieved document contexts.",
            "fields": {
                field: {
                    "description": _FIELD_QUERIES[field],
                    "context": data["context"],
                }
                for field, data in field_contexts.items()
            },
        }
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, indent=2)},
        ]
        try:
            response = await self.acompletion(
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = getattr(response.choices[0].message, "content", None) or "{}"
            llm_output: dict[str, Any] = json.loads(content)
        except Exception as exc:
            logger.warning("[DocIntelligenceAgent] LLM call failed: %s", exc)
            return _empty_result()

        # 4. Build DocExtractionResult from LLM output.
        stage_a_partial: dict[str, Any] = {}
        stage_b_partial: dict[str, Any] = {}
        field_confidence: dict[str, float] = {}
        field_sources: dict[str, str] = {}
        missing: list[str] = []

        for field in _FIELD_QUERIES:
            entry = llm_output.get(field, {})
            if not isinstance(entry, dict):
                missing.append(field)
                continue
            value = entry.get("value")
            confidence = float(entry.get("confidence", 0.0))
            if value is None or confidence < 0.35:
                missing.append(field)
                continue
            target = stage_a_partial if field in _STAGE_A_FIELDS else stage_b_partial
            target[field] = value
            field_confidence[field] = confidence
            ctx = field_contexts.get(field, {})
            field_sources[field] = ctx.get("best_source", "document")

        return {
            "stage_a_partial": stage_a_partial,
            "stage_b_partial": stage_b_partial,
            "field_confidence": field_confidence,
            "field_sources": field_sources,
            "missing_fields": missing,
        }
