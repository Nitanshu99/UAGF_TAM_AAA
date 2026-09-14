"""_invoke() binds the dispatch's engagement id for the duration of agent.process()."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from aaa.agents.tier1.phases.agent_runner.logger import _invoke
from aaa.observability.trace_context import current_engagement_id


@pytest.mark.asyncio
async def test_invoke_binds_engagement_id_from_dispatch():
    """The agent observes the bound id inside process(), cleared afterward."""
    seen = {}

    class _Agent:
        """Stub agent recording the bound engagement id during process()."""

        async def process(self, _dispatch):
            """Record the currently-bound engagement id."""
            seen["during"] = current_engagement_id()
            return {}

    dispatch = {"declaration_summary": {"engagement_id": "eng-42"}}
    await _invoke(_Agent(), dispatch, timeout=5)
    assert seen["during"] == "eng-42"
    assert current_engagement_id() is None


@pytest.mark.asyncio
async def test_invoke_without_engagement_id_binds_none():
    """A dispatch with no declared engagement id binds nothing (no crash)."""
    seen = {}

    class _Agent:
        """Stub agent recording the bound engagement id during process()."""

        async def process(self, _dispatch):
            """Record the currently-bound engagement id."""
            seen["during"] = current_engagement_id()
            return {}

    await _invoke(_Agent(), SimpleNamespace(), timeout=5)
    assert seen["during"] is None
