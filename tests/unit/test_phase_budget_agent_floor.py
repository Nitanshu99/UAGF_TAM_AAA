"""Phase 5's budget must be funded from Phase 5's work, not the pool's.

The estimator reads recent phase calls whoever made them, which is right while
payloads are comparable. On the 2026-09-09 Mariposa re-run against a real S5
export they were not: the GovernanceAgent's prompt was **181,595 tokens against
~44,700 for the mock fixture**, and 289 s a call against 87–123 s. Phase 5 was
handed 415 s — 2 × a 207.8 s ScopeAgent call — abandoned at it, and recorded
Art. 9, 12, 14, 17 and 72 as INSUFFICIENT_EVIDENCE. Five articles unassessed
because the phase was funded from a measurement of different work.
"""
from __future__ import annotations

import pytest

from aaa.platform.phase_budget import (
    AGENT_MIN_PHASE_SECONDS,
    CALLS_PER_PHASE,
    MAX_PHASE_SECONDS,
    MIN_PHASE_SECONDS,
    phase_timeout,
    reset,
)

#: What the run actually measured, once the call was allowed to finish.
MEASURED_P5_SECONDS = 289.0

#: What the pooled estimate offered it instead.
POOLED_ESTIMATE_SECONDS = 207.8


@pytest.fixture(autouse=True)
def _clean_observations():
    """Each test sizes a budget from a known sample, not the last test's."""
    reset()
    yield
    reset()


def test_the_budget_that_lost_five_articles_would_now_cover_the_call():
    """The acceptance criterion, stated as an assertion."""
    assert phase_timeout("GovernanceAgent") >= MEASURED_P5_SECONDS * CALLS_PER_PHASE


def test_the_floor_applies_before_anything_has_been_measured():
    """Phase 5 runs once per engagement, so its cold start is its only start."""
    assert phase_timeout("GovernanceAgent") == int(AGENT_MIN_PHASE_SECONDS["GovernanceAgent"])


def test_a_pooled_estimate_below_the_floor_no_longer_wins():
    """This is the exact number that abandoned the phase."""
    from aaa.platform.phase_budget import observe
    from aaa.platform.phase_budget.deadline import bind_phase_deadline

    with bind_phase_deadline(900):
        observe("GovernanceAgent", POOLED_ESTIMATE_SECONDS)
    assert phase_timeout("GovernanceAgent") > POOLED_ESTIMATE_SECONDS * CALLS_PER_PHASE


def test_every_other_agent_keeps_the_global_floor():
    """The floor is per-agent precisely so it does not inflate every phase."""
    # ModelValidator is deliberately absent: like GovernanceAgent it now
    # carries its own floor, because most of its cost is tooling the
    # LLM-call estimator cannot see.
    for agent in ("ScopeAgent", "DataAuditor", "Verifier", None):
        assert phase_timeout(agent) == int(MIN_PHASE_SECONDS)


def test_a_higher_measurement_still_wins_over_the_floor():
    """It is a floor, not an override — the estimator still leads when it leads."""
    from aaa.platform.phase_budget import observe
    from aaa.platform.phase_budget.deadline import bind_phase_deadline

    with bind_phase_deadline(900):
        observe("GovernanceAgent", 400.0)
    assert phase_timeout("GovernanceAgent") == int(400.0 * CALLS_PER_PHASE)


def test_the_ceiling_still_binds():
    """A per-agent floor must not become a way past MAX_PHASE_SECONDS."""
    from aaa.platform.phase_budget import observe
    from aaa.platform.phase_budget.deadline import bind_phase_deadline

    with bind_phase_deadline(2000):
        observe("GovernanceAgent", 1500.0)
    assert phase_timeout("GovernanceAgent") == int(MAX_PHASE_SECONDS)
    assert all(v <= MAX_PHASE_SECONDS for v in AGENT_MIN_PHASE_SECONDS.values())
