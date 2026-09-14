"""CGSA (S4) payload envelope types — §5.4 binding contract."""
from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

from aaa.platform.state.cgsa import (
    BlockingFinding,
    FollowUpItem,
    LowConfidenceControl,
    PositiveFinding,
    RemediationItem,
)


class CGSAMetadata(TypedDict):
    """Assessment identity block of the CGSA payload."""
    assessment_id: str
    organisation_name: str
    system_under_audit: str
    cgsa_version: str
    assessment_timestamp: str
    risk_tier: str
    document_sources: list[str]
    uagf_gmm_version: str


class CGSAOverallScores(TypedDict):
    """Headline maturity scores of the CGSA payload."""
    composite_maturity_score: float
    composite_maturity_label: str
    eu_ai_act_coverage_pct: float
    csp_satisfiable: bool
    governance_verdict: Literal["compliant", "partially_compliant", "non_compliant"]
    controls_assessed: int
    controls_meeting: int
    controls_below_threshold: int


class CGSAAAPhase5Handoff(TypedDict):
    """The §5.4 hand-off surface consumed by the Phase 5 GovernanceAgent."""
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
