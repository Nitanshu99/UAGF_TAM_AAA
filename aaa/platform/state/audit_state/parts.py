"""Composable sections of the :class:`AuditState` TypedDict."""
from __future__ import annotations

from typing import Any, Literal, NotRequired, Optional, TypedDict

from aaa.platform.state.cgsa import (
    BlockingFinding,
    FollowUpItem,
    LowConfidenceControl,
    PositiveFinding,
)
from aaa.platform.state.cgsa.payload import CGSAPayload
from aaa.platform.state.dossier import ClientSubmission
from aaa.platform.state.findings import AnnexIIIEntry, Art43Decision, ArtefactRef


class AuditStateIdentity(TypedDict):
    """Engagement identity, declared values, and Phase 1 verified values."""
    engagement_id: str
    client_doc_collection: Optional[str]  # Qdrant collection for per-engagement client docs.
    client_submission: ClientSubmission
    scope_gate: NotRequired[dict[str, Any]]  # Pre-intake gate result (ScopeGateResult fields)
    declared_modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
    declared_risk_tier: Literal["high", "limited", "minimal", "gpai"]
    declared_annex_iii_sections: list[Literal["1", "2", "3", "4", "5", "6", "7", "8"]]
    risk_tier: Literal["prohibited", "high", "limited", "minimal", "gpai"]
    annex_iii_mapping: list[AnnexIIIEntry]
    modality: Literal["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"]
    deployment_context: Literal["b2b", "b2c", "public_sector", "internal"]
    is_llm_or_agentic: bool
    provider_elects_third_party: bool
    harmonised_standards_applied: bool
    annex_i_section_a_acts: list[str]
    declaration_verification: dict[str, Literal["match", "mismatch", "corrected", "not_verifiable"]]
    art43_decision: Optional[Art43Decision]
    phase_artefacts: dict[str, ArtefactRef]


class AuditStateCGSA(TypedDict):
    """The S4 CGSA hand-off surface (§5.4)."""
    cgsa_payload: Optional[CGSAPayload]
    # Which assessment was read, whether it is an evaluated export, and whether it
    # superseded the declared one (T-20260914-062).
    cgsa_source: Optional[dict]
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
