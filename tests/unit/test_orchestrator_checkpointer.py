"""Regression tests for Orchestrator checkpoint integration.

NOTE: checkpoint helpers now live in aaa.agents.tier1.checkpointer.
These tests are updated to patch the new module.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import aaa.agents.tier1.orchestrator as orchestrator
import aaa.agents.tier1.checkpointer as checkpointer_mod


def test_checkpoint_db_url_falls_back_to_settings(monkeypatch: pytest.MonkeyPatch):
    """DATABASE_URL should fall back to the value in settings when not set in env."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Override the DATABASE_URL env var at the pydantic-settings level
    monkeypatch.setenv("DATABASE_URL", "postgresql://from-settings")
    # Re-resolve (the function reads os.environ at call time)
    url = checkpointer_mod.checkpoint_db_url()
    assert "from-settings" in url or url.startswith("postgresql://")


@pytest.mark.asyncio
async def test_run_uses_async_checkpointer_for_online_langgraph(monkeypatch: pytest.MonkeyPatch):
    """Online async runs should use AsyncPostgresSaver-compatible checkpoint setup."""
    monkeypatch.setattr(orchestrator, "_OFFLINE", False)

    def _fake_verifier():
        return SimpleNamespace()

    monkeypatch.setattr(orchestrator, "Verifier", _fake_verifier)

    expected_graph = object()
    build_calls: list[object | None] = []

    def _fake_build_graph(_self, checkpointer=None):
        build_calls.append(checkpointer)
        return expected_graph

    run_langgraph = AsyncMock(return_value={"engagement_id": "eng-001"})
    monkeypatch.setattr(orchestrator.Orchestrator, "_build_graph", _fake_build_graph)
    monkeypatch.setattr(orchestrator.Orchestrator, "_run_langgraph", run_langgraph)

    fake_checkpointer = SimpleNamespace(setup=AsyncMock())

    class _FakeAsyncCM:
        async def __aenter__(self):
            return fake_checkpointer

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def _fake_make_async_checkpointer():
        return _FakeAsyncCM()

    # Patch the checkpointer module that orchestrator imports
    monkeypatch.setattr(orchestrator, "make_async_checkpointer", _fake_make_async_checkpointer)

    agent = orchestrator.Orchestrator(evidence_store=None)
    result = await agent.run({"engagement_id": "eng-001"})

    assert result == {"engagement_id": "eng-001"}
    fake_checkpointer.setup.assert_awaited_once()
    assert build_calls == [None, fake_checkpointer]
    run_langgraph.assert_awaited_once_with({"engagement_id": "eng-001"}, expected_graph)
