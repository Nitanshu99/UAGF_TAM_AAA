"""
aaa.agents.tier1.checkpointer — Checkpoint persistence factory.

Provides:
  - ``_InMemoryCheckpointer``: lightweight in-process replacement for the
    LangGraph PostgresSaver.
  - ``make_checkpointer()``: returns the in-memory saver (sequential runs).
  - ``make_async_checkpointer()``: returns the async Postgres saver (production).
  - ``checkpoint_db_url()``: resolves DATABASE_URL from env / settings.
"""
from __future__ import annotations

import os
from typing import Any


class _InMemoryCheckpointer:
    """In-process replacement for LangGraph checkpoint persistence."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def put(self, thread_id: str, state: dict) -> None:
        """Store a copy of *state* under *thread_id*."""
        self._store[thread_id] = dict(state)

    def get(self, thread_id: str) -> dict | None:
        """Return the stored state for *thread_id*, or ``None``."""
        return self._store.get(thread_id)


def checkpoint_db_url() -> str:
    """Resolve the Postgres connection string from env / settings."""
    from aaa.settings import settings

    return (
        os.environ.get("DATABASE_URL")
        or settings.database_url
        or "postgresql://aaa:aaa@localhost:5432/aaa"
    )


def make_checkpointer() -> _InMemoryCheckpointer:
    """Return the in-memory fallback used for sequential runs."""
    return _InMemoryCheckpointer()


def make_async_checkpointer():  # pragma: no cover
    """Return the async Postgres saver context manager for online LangGraph runs."""
    # The postgres saver ships in an optional langgraph extra.
    # pylint: disable=no-name-in-module
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # type: ignore

    return AsyncPostgresSaver.from_conn_string(checkpoint_db_url())


__all__ = [
    "_InMemoryCheckpointer",
    "checkpoint_db_url",
    "make_checkpointer",
    "make_async_checkpointer",
]
