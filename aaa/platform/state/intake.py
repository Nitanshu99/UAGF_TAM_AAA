"""Stage A triage form types (§6 Stage 0)."""
from __future__ import annotations

from typing import Literal, NotRequired, TypedDict


class ComponentModality(TypedDict):
    """One AI component of the system under audit (§6.2 composite routing).

    A system may carry more than one AI component — an embedding ranker beside
    a generative model, say. ``declared_modality`` names only the component that
    sets the highest obligation, so the phase plan is derived from this list
    when present.
    """
    id: str
    modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
    role: NotRequired[str]


class StageATriage(TypedDict):
    """~20-question form submitted at the start of each engagement (§6 Stage 0)."""
    provider_name: str
    deployer_name: str | None
    system_name: str
    version: str
    intended_purpose: str
    declared_modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
    component_modalities: NotRequired[list[ComponentModality]]
    declared_risk_tier: Literal["high", "limited", "minimal", "gpai"]
    declared_annex_iii_sections: list[Literal["1", "2", "3", "4", "5", "6", "7", "8"]]
    deployment_context: Literal["b2b", "b2c", "public_sector", "internal"]
    provider_elects_third_party: bool
    gdpr_overlap: bool
    gpai_general_purpose: bool
    special_category_data: bool
    art43_preview: str | None
    cgsa_assessment_id: str | None
    # ── Optional FLI-derived scoping fields (pre-Stage-A questionnaire) ─────────
    # Source: FLI "EU AI Act Compliance Checker" v1.0 (2025-07-28).
    # All fields are NotRequired for backward compatibility with legacy fixtures.
    entity_type: NotRequired[list[Literal[
        "provider", "deployer", "distributor", "importer",
        "product_manufacturer", "authorised_representative"
    ]]]
    art25_status_change: NotRequired[list[Literal[
        "name_trademark", "intended_purpose_change",
        "substantial_modification", "none"
    ]]]
    annex_i_section_a: NotRequired[list[str]]
    annex_i_section_b: NotRequired[list[str]]
    third_party_ca_legally_required: NotRequired[bool]
    art6_derogation_claimed: NotRequired[bool]
    art6_derogation_rationale: NotRequired[str | None]
    territorial_scope: NotRequired[list[Literal[
        "placed_on_eu_market", "gpai_placed_on_eu_market", "established_in_eu",
        "importer_in_eu", "output_used_in_eu", "none"
    ]]]
    gpai_systemic_risk: NotRequired[bool]
    art2_exclusion: NotRequired[Literal[
        "military", "third_country_law_enforcement", "research_and_development",
        "open_source", "personal_use", "none"
    ] | None]
    art5_prohibited_practices: NotRequired[list[str]]
    art50_transparency_triggers: NotRequired[list[str]]
    is_public_body_or_public_service: NotRequired[bool]
