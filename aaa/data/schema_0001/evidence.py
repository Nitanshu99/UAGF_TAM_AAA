"""Revision 0001 — the ``evidence_artefacts`` table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

_JSONB = postgresql.JSONB(astext_type=sa.Text())


def create_evidence_artefacts() -> None:
    """Create the ``evidence_artefacts`` EvidenceStore index table (§5.2)."""
    op.create_table(
        "evidence_artefacts",
        sa.Column("uri", sa.Text, primary_key=True),
        sa.Column("engagement_id", sa.String(36),
                  sa.ForeignKey("engagements.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("artefact_type", sa.String(80), nullable=False),
        sa.Column("agent_name", sa.String(80), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("content", _JSONB, nullable=False),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_evidence_engagement_id", "evidence_artefacts",
                    ["engagement_id"])
