"""CGSA (S4) finding and remediation item types — §5.4 binding contract."""
from __future__ import annotations

from typing import Literal, Optional, TypedDict

from aaa.platform.state.findings import Materiality


class BlockingFinding(TypedDict):
    """Below-threshold CGSA control blocking Phase 5."""
    control_id: str
    control_name: str
    gap_detail: str
    gap_severity: str
    eu_ai_act_articles: list[str]


class PositiveFinding(TypedDict):
    """CGSA control meeting or exceeding its maturity target."""
    control_id: str
    control_name: str
    evidence_summary: str
    maturity_label: str


class LowConfidenceControl(TypedDict):
    """CGSA control whose self-assessment confidence is below 0.60."""
    control_id: str
    control_name: str
    confidence: float
    evidence_summary: str


class FollowUpItem(TypedDict):
    """Recommended follow-up action lifted from the CGSA hand-off."""
    item_id: str
    description: str
    urgency: Literal["required_before_report_completion", "recommended", "optional"]
    assigned_to: Optional[str]


class RemediationItem(TypedDict, total=False):
    """One prioritised remediation-roadmap entry."""
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
    domain_id: Optional[str]
    # Carried verbatim from the CGSA roadmap row (T-20260913-006).
    control_name: str
    eu_ai_act_article: str
    current_score: Optional[int]
    target_score: Optional[int]
    effort_estimate: Optional[str]
    timeline_weeks: Optional[int]
