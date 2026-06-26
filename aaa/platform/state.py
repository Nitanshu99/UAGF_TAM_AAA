from __future__ import annotations
from typing import TypedDict, Literal, Any, Optional, NotRequired
from datetime import datetime

class StageATriage(TypedDict):
    """~20-question form submitted at the start of each engagement (§6 Stage 0)."""
    provider_name: str
    deployer_name: str | None
    system_name: str
    version: str
    intended_purpose: str
    declared_modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
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

class AnnexIVDossier(TypedDict):
    """Annex IV §1–§9 technical documentation uploaded in Stage B."""
    general_description: str
    model_type: str
    design_process: str
    training_data_description: str
    data_governance_measures: str
    monitoring_measures: str
    logging_capabilities: str
    accuracy_metrics: dict[str, float]
    robustness_metrics: dict[str, float] | None
    risk_management_file_uri: str | None
    lifecycle_change_log: list[str]
    harmonised_standards: list[str]
    other_standards: list[str]
    eu_doc_uri: str | None
    post_market_plan_uri: str | None
    system_prompt_uri: str | None
    rag_manifest_uri: str | None
    tool_inventory: list[str] | None
    guardrail_config_uri: str | None
    golden_set_uri: str | None
    # ── Independent-analysis inputs (populated by UI upload flow / fixtures) ─────
    # URIs to the real artefacts the audit re-runs against, and a minimal data
    # dictionary so agents can split X/y and scope protected-attribute fairness
    # testing. All NotRequired for backward compatibility with legacy fixtures.
    model_artifact_uri: NotRequired[str | None]
    training_dataset_uri: NotRequired[str | None]
    evaluation_dataset_uri: NotRequired[str | None]
    target_column: NotRequired[str | None]
    positive_label: NotRequired[Any]
    sensitive_feature_columns: NotRequired[list[str] | None]
    feature_columns: NotRequired[list[str] | None]
    data_dictionary: NotRequired[dict[str, Any] | None]

class StageCAccess(TypedDict):
    """Scoped live-system access credentials granted in Stage C."""
    read_only_api_endpoint: str | None
    credential_ref: str
    access_scope: list[str]
    access_expiry_utc: str
    revocation_webhook: str | None

class ClientSubmission(TypedDict):
    """Root intake bundle — union of Stage A + B + C artefacts."""
    stage_a: StageATriage
    stage_b: AnnexIVDossier
    stage_c: StageCAccess | None
    intake_completeness_score: float

Materiality = Literal[
    "material",
    "possibly_material",
    "not_material",
]

class AnnexIIIEntry(TypedDict):
    annex_iii_section: Literal["1", "2", "3", "4", "5", "6", "7", "8"]
    section_title: str
    use_case_marker: str
    confidence: float
    provenance: Literal["client_declared", "phase1_verified", "phase1_corrected", "phase1_rejected"]
    derogation_claimed: bool
    derogation_rationale: str | None

class Art43Decision(TypedDict):
    procedure: Literal["annex_vi_internal_control", "annex_vii_notified_body", "not_applicable"]
    rationale: str

class ArtefactRef(TypedDict):
    uri: str
    sha256: str
    template_id: str

# ──────────────────────────────────────────────────────────────────────────────
# CGSA (S4) payload types — §5.4 binding contract
# ──────────────────────────────────────────────────────────────────────────────

class BlockingFinding(TypedDict):
    control_id: str
    control_name: str
    gap_detail: str
    gap_severity: str
    eu_ai_act_articles: list[str]

class PositiveFinding(TypedDict):
    control_id: str
    control_name: str
    evidence_summary: str
    maturity_label: str

class LowConfidenceControl(TypedDict):
    control_id: str
    control_name: str
    confidence: float
    evidence_summary: str

class FollowUpItem(TypedDict):
    item_id: str
    description: str
    urgency: Literal["required_before_report_completion", "recommended", "optional"]
    assigned_to: Optional[str]

class RemediationItem(TypedDict, total=False):
    rank: int
    control_id: str
    gap_detail: str
    gap_severity: str
    recommended_action: str
    target_date: Optional[str]
    materiality: Materiality
    materiality_rationale: str
    assigned_owner: Optional[str]
    deadline_weeks: Optional[int]
    priority_label: Literal["immediate", "short_term", "medium_term", "long_term"] | None

class CGSAMetadata(TypedDict):
    assessment_id: str
    organisation_name: str
    system_under_audit: str
    cgsa_version: str
    assessment_timestamp: str
    risk_tier: str
    document_sources: list[str]
    uagf_gmm_version: str

class CGSAOverallScores(TypedDict):
    composite_maturity_score: float
    composite_maturity_label: str
    eu_ai_act_coverage_pct: float
    csp_satisfiable: bool
    governance_verdict: Literal["compliant", "partially_compliant", "non_compliant"]
    controls_assessed: int
    controls_meeting: int
    controls_below_threshold: int

class CGSAAAPhase5Handoff(TypedDict):
    phase5_verdict: Literal["PASS", "PASS_WITH_OBSERVATIONS", "FAIL"]
    phase5_narrative_summary: str
    blocking_findings_count: int
    blocking_findings: list[BlockingFinding]
    positive_findings: list[PositiveFinding]
    low_confidence_controls: list[LowConfidenceControl]
    aaa_recommended_follow_up: list[FollowUpItem]
    cgsa_report_url: Optional[str]

class CGSAPayload(TypedDict):
    """Parsed + validated S4 CGSA JSON payload consumed by Phase 5."""
    metadata: CGSAMetadata
    overall_scores: CGSAOverallScores
    domains: list[dict[str, Any]]
    eu_ai_act_compliance_matrix: dict[str, Any]
    hard_constraint_results: dict[str, Any]
    remediation_roadmap: list[RemediationItem]
    aaa_phase5_handoff: CGSAAAPhase5Handoff

# ──────────────────────────────────────────────────────────────────────────────
# Compliance matrix value types
# ──────────────────────────────────────────────────────────────────────────────

Article = str   # e.g. "Art.9", "Art.43", "Annex_III"
Verdict = Literal[
    "PASS", "PASS_WITH_OBSERVATIONS", "FAIL",
    "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE", "PENDING",
]

class Finding(TypedDict, total=False):
    finding_id: str
    phase: str
    phase_id: str
    article: str
    description: str
    severity: Literal["critical", "major", "minor", "observation"]
    materiality: Materiality
    materiality_rationale: str
    evidence_uri: Optional[str]

# ──────────────────────────────────────────────────────────────────────────────
# AuditState — full LangGraph typed dict threaded through the graph (§5.1)
# ──────────────────────────────────────────────────────────────────────────────

class DocExtractionResult(TypedDict):
    """Result returned by DocIntelligenceAgent after reading customer uploads."""
    stage_a_partial: dict[str, Any]
    stage_b_partial: dict[str, Any]
    field_confidence: dict[str, float]   # field_name → 0.0–1.0
    field_sources: dict[str, str]        # field_name → "filename, p. N"
    missing_fields: list[str]


class AuditState(TypedDict):
    # --- engagement identity ---
    engagement_id: str
    client_doc_collection: Optional[str]  # Qdrant collection for per-engagement client docs.
    client_submission: ClientSubmission
    scope_gate: NotRequired[dict[str, Any]]  # Pre-intake gate result (ScopeGateResult fields)

    # --- declared values (from Stage A — immutable after Stage A close) ---
    declared_modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
    declared_risk_tier: Literal["high", "limited", "minimal", "gpai"]
    declared_annex_iii_sections: list[Literal["1", "2", "3", "4", "5", "6", "7", "8"]]

    # --- Phase 1 verified values ---
    risk_tier: Literal["prohibited", "high", "limited", "minimal", "gpai"]
    annex_iii_mapping: list[AnnexIIIEntry]
    modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
    deployment_context: Literal["b2b", "b2c", "public_sector", "internal"]
    is_llm_or_agentic: bool
    provider_elects_third_party: bool
    harmonised_standards_applied: bool

    # --- declared-vs-verified diff ---
    declaration_verification: dict[str, Literal["match", "mismatch", "corrected", "not_verifiable"]]

    # --- Article 43 (§3.5) ---
    art43_decision: Optional[Art43Decision]

    # --- artefact graph ---
    phase_artefacts: dict[str, ArtefactRef]

    # --- S4 CGSA hand-off (§5.4) ---
    cgsa_payload: Optional[CGSAPayload]
    cgsa_schema_version: Optional[str]
    cgsa_composite_maturity_score: Optional[float]
    cgsa_composite_maturity_label: Optional[str]
    cgsa_domain_scores: Optional[dict]
    cgsa_eu_ai_act_coverage_pct: Optional[float]
    cgsa_csp_satisfiable: Optional[bool]
    cgsa_governance_verdict: Optional[Literal["compliant", "partially_compliant", "non_compliant"]]
    cgsa_phase5_verdict: Optional[Literal["PASS", "PASS_WITH_OBSERVATIONS", "FAIL"]]
    cgsa_phase5_narrative: Optional[str]
    cgsa_blocking_findings: list[BlockingFinding]
    cgsa_positive_findings: list[PositiveFinding]
    cgsa_low_confidence_controls: list[LowConfidenceControl]
    cgsa_recommended_follow_up: list[FollowUpItem]
    cgsa_report_url: Optional[str]
    cgsa_risk_tier_match: Optional[bool]

    # --- compliance assembly ---
    compliance_matrix: dict[Article, Verdict]
    blocking_findings: list[Finding]
    positive_findings: list[Finding]
    remediation_roadmap: list[RemediationItem]
    material_findings_count: Optional[int]
    possibly_material_findings_count: Optional[int]
    # Articles whose required independent analysis could not be performed (missing
    # artefact, unscored eval set, agent fallback). Accumulated across phases; the
    # compliance matrix marks these INSUFFICIENT_EVIDENCE (never PASS). (§WS5/WS8)
    insufficient_evidence_articles: NotRequired[list[str]]

    # --- verification & verdict ---
    verifier_critiques: dict[str, dict[str, Any]]
    intake_completeness_score: Optional[float]
    completeness_score: Optional[float]
    regulatory_coverage_pct: Optional[float]
    final_verdict: Optional[Literal["PASS", "PASS_WITH_OBSERVATIONS", "FAIL"]]
    auditor_opinion: Optional[dict]
