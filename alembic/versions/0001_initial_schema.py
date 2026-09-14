"""Initial schema: engagements, evidence, langgraph_checkpoints

Revision ID: 0001
Revises:
Create Date: 2026-05-24

Creates:
  - engagements          — audit engagement records (§14.5)
  - evidence_artefacts   — EvidenceStore index (§5.2)
  - langgraph_checkpoints — LangGraph PostgresSaver checkpoint table (§6)

The table bodies live in :mod:`aaa.data.schema_0001` (frozen for this
revision) so the revision file stays small; alembic runs with the repo root
on ``sys.path`` (``prepend_sys_path = .``), so the import always resolves.
"""
from __future__ import annotations

from aaa.data.schema_0001 import (
    create_engagements,
    create_evidence_artefacts,
    create_langgraph_checkpoints,
)
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the three initial tables."""
    create_engagements()
    create_evidence_artefacts()
    create_langgraph_checkpoints()


def downgrade() -> None:
    """Drop the three initial tables in dependency order."""
    op.drop_table("langgraph_checkpoints")
    op.drop_table("evidence_artefacts")
    op.drop_table("engagements")
