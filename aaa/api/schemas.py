"""aaa.api.schemas — Pydantic request/response models for the AAA REST API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EngagementCreate(BaseModel):
    """Request body for POST /api/v1/engagements."""

    engagement_id: str | None = Field(
        None, description="Optional slug/UUID; auto-generated if omitted."
    )
    provider_name: str = Field(..., description="AI system provider name.")
    system_name: str = Field(..., description="AI system name.")
    declared_risk_tier: str = Field(
        ..., description="high | limited | minimal | gpai"
    )
    cgsa_assessment_id: str | None = Field(
        None, description="Optional S4 CGSA assessment ID for Phase 5."
    )


class EngagementOut(BaseModel):
    """Engagement resource returned by the API."""

    engagement_id: str
    provider_name: str
    system_name: str
    declared_risk_tier: str
    cgsa_assessment_id: str | None
    status: str
    created_at: str


class IntakePayload(BaseModel):
    """Stage A/B/C payload submission for an engagement."""

    stage_a: dict[str, Any]
    stage_b: dict[str, Any]
    stage_c: dict[str, Any] | None = None


class RunResult(BaseModel):
    """Result returned after running an engagement."""

    engagement_id: str
    status: str
    final_verdict: str | None
    regulatory_coverage_pct: float | None


class ReportSummary(BaseModel):
    """KPI summary and report URIs returned by GET /report."""

    engagement_id: str
    final_verdict: str | None
    kpis: dict[str, Any]
    t18_json_uri: str
    pdf_uri: str | None


__all__ = [
    "EngagementCreate",
    "EngagementOut",
    "IntakePayload",
    "RunResult",
    "ReportSummary",
]
