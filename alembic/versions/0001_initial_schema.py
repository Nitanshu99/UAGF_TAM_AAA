"""Initial schema: engagements, evidence, langgraph_checkpoints

Revision ID: 0001
Revises:
Create Date: 2026-05-24

Creates:
  - engagements          — audit engagement records (§14.5)
  - evidence_artefacts   — EvidenceStore index (§5.2)
  - langgraph_checkpoints — LangGraph PostgresSaver checkpoint table (§6)
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── engagements ────────────────────────────────────────────────────────
    op.create_table(
        "engagements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_name", sa.Text, nullable=False),
        sa.Column("system_name", sa.Text, nullable=False),
        sa.Column("declared_risk_tier", sa.String(20), nullable=False),
        sa.Column("cgsa_assessment_id", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="created",
        ),
        sa.Column("final_verdict", sa.String(30), nullable=True),
        sa.Column("intake_completeness_score", sa.Float, nullable=True),
        sa.Column("completeness_score", sa.Float, nullable=True),
        sa.Column("regulatory_coverage_pct", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "phase_artefacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "compliance_matrix",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_index("ix_engagements_status", "engagements", ["status"])
    op.create_index(
        "ix_engagements_created_at", "engagements", ["created_at"]
    )

    # ── evidence_artefacts ─────────────────────────────────────────────────
    op.create_table(
        "evidence_artefacts",
        sa.Column("uri", sa.Text, primary_key=True),
        sa.Column(
            "engagement_id",
            sa.String(36),
            sa.ForeignKey("engagements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("artefact_type", sa.String(80), nullable=False),
        sa.Column("agent_name", sa.String(80), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column(
            "content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "stored_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_evidence_engagement_id",
        "evidence_artefacts",
        ["engagement_id"],
    )

    # ── langgraph_checkpoints ──────────────────────────────────────────────
    # Minimal schema compatible with LangGraph's PostgresSaver.
    op.create_table(
        "langgraph_checkpoints",
        sa.Column("thread_id", sa.Text, nullable=False),
        sa.Column("checkpoint_ns", sa.Text, nullable=False, server_default=""),
        sa.Column("checkpoint_id", sa.Text, nullable=False),
        sa.Column(
            "parent_checkpoint_id", sa.Text, nullable=True
        ),
        sa.Column("type", sa.Text, nullable=True),
        sa.Column(
            "checkpoint",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint(
            "thread_id", "checkpoint_ns", "checkpoint_id"
        ),
    )


def downgrade() -> None:
    op.drop_table("langgraph_checkpoints")
    op.drop_table("evidence_artefacts")
    op.drop_table("engagements")
