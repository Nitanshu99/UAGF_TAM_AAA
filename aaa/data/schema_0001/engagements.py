"""Revision 0001 — the ``engagements`` table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

_JSONB = postgresql.JSONB(astext_type=sa.Text())


def create_engagements() -> None:
    """Create the ``engagements`` table (§14.5) and its indexes."""
    op.create_table(
        "engagements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_name", sa.Text, nullable=False),
        sa.Column("system_name", sa.Text, nullable=False),
        sa.Column("declared_risk_tier", sa.String(20), nullable=False),
        sa.Column("cgsa_assessment_id", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="created"),
        sa.Column("final_verdict", sa.String(30), nullable=True),
        sa.Column("intake_completeness_score", sa.Float, nullable=True),
        sa.Column("completeness_score", sa.Float, nullable=True),
        sa.Column("regulatory_coverage_pct", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("phase_artefacts", _JSONB, nullable=True),
        sa.Column("compliance_matrix", _JSONB, nullable=True),
    )
    op.create_index("ix_engagements_status", "engagements", ["status"])
    op.create_index("ix_engagements_created_at", "engagements", ["created_at"])
