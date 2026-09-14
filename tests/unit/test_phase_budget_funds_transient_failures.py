"""T-20260913-102: a phase budget funds the retry a failing provider forces.

Case 05's Phase 2 got 300 s from a 95.3 s call; its seed call failed after 92.6 s,
the retry delivered at 216.1 s, and the re-prompt after it ran out of time.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from aaa.platform.phase_budget import (
    CALLS_PER_PHASE,
    bind_phase_deadline,
    observe,
    observe_failure,
    phase_timeout,
    reset,
    slowest_failure,
)
from aaa.platform.transient_retry.ladder import ladder


class _ServiceUnavailableError(Exception):
    """``litellm.ServiceUnavailableError`` by type name: transient."""


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    """Process-global readings start empty; backoff does not really sleep."""
    reset()
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    yield
    reset()


def test_each_funded_call_carries_the_slowest_recent_failure() -> None:
    """Case 05's readings: 2 × (95.3 + 96.5) = 383 s, enough for 216 s + a re-prompt."""
    with bind_phase_deadline(600):
        observe("ScopeAgent", 95.3)
        observe_failure(96.5)
    assert phase_timeout("DataAuditor") == int((95.3 + 96.5) * CALLS_PER_PHASE) == 383


def test_a_failure_outside_a_phase_does_not_size_one() -> None:
    """The Orchestrator's and Verifier's failures are not phase costs."""
    observe_failure(120.0)
    assert slowest_failure() is None


def test_the_ladder_records_a_retried_failure_inside_a_phase() -> None:
    """A retried overload inside a deadline becomes a reading."""
    calls: list[int] = []

    async def provider(**_kwargs) -> str:
        calls.append(1)
        if len(calls) == 1:
            raise _ServiceUnavailableError("Service temporarily overloaded")
        return "answered"

    async def phase() -> tuple:
        with bind_phase_deadline(600):
            return await ladder(provider, {"model": "m"})

    assert asyncio.run(phase())[0] == "answered"
    assert slowest_failure() is not None
