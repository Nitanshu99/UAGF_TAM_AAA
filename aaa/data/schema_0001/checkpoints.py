"""Revision 0001 — the ``langgraph_checkpoints`` table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

_JSONB = postgresql.JSONB(astext_type=sa.Text())


def create_langgraph_checkpoints() -> None:
    """Create the LangGraph ``PostgresSaver``-compatible checkpoint table (§6)."""
    op.create_table(
        "langgraph_checkpoints",
        sa.Column("thread_id", sa.Text, nullable=False),
        sa.Column("checkpoint_ns", sa.Text, nullable=False, server_default=""),
        sa.Column("checkpoint_id", sa.Text, nullable=False),
        sa.Column("parent_checkpoint_id", sa.Text, nullable=True),
        sa.Column("type", sa.Text, nullable=True),
        sa.Column("checkpoint", _JSONB, nullable=False),
        sa.Column("metadata", _JSONB, nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", "checkpoint_id"),
    )
