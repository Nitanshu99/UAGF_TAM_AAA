"""Stage A field-extraction queries (system identity and classification)."""
from __future__ import annotations

#: Field names that belong to the Stage A triage form.
STAGE_A_FIELDS: frozenset[str] = frozenset({
    "provider_name", "system_name", "version",
    "intended_purpose", "declared_modality", "declared_risk_tier",
})

#: Field → plain-English search query; used both to search the Qdrant
#: collection and as field descriptions in the batched LLM prompt.
STAGE_A_QUERIES: dict[str, str] = {
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
        "time_series, llm (large language model), agentic (autonomous agent), "
        "gpai (foundation model)."
    ),
    "declared_risk_tier": (
        "Is this AI system classified as high-risk, limited risk, minimal risk, or "
        "general-purpose AI (gpai) under the EU AI Act?"
    ),
}
