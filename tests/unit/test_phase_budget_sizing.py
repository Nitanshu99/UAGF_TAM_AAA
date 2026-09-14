"""Fix 34 — the phase budget is derived from measured latency, not a literal (R1).

The run's own numbers are the fixtures: 216.8 s was Phase 1's slowest call in
[case 01](local/assessments/run_2026-09-03/case_01_finclear_gmbh.md) #004
and 347.8 s was the slowest phase-agent call in the whole five-case run.

These exercise the *general* estimator, so they name an agent that carries no
entry in ``AGENT_MIN_PHASE_SECONDS``. Naming one that does would assert the
global floor against a per-agent floor that is deliberately higher, and the
failure would read as a broken estimator rather than a mis-chosen fixture —
see :mod:`tests.unit.test_phase_budget_agent_floor` for that half.
"""
from __future__ import annotations

import pytest

from aaa.platform.phase_budget import (
    CALLS_PER_PHASE,
    MAX_PHASE_SECONDS,
    MIN_PHASE_SECONDS,
    bind_phase_deadline,
    observe,
    phase_timeout,
    reset,
    slowest_call,
)
from aaa.platform.phase_budget.observed import WINDOW


@pytest.fixture(autouse=True)
def _clean():
    """The observatory is process-global; each test starts from nothing."""
    reset()
    yield
    reset()


def _seen(agent: str, *seconds: float) -> None:
    """Record calls as a phase would — inside a bound deadline."""
    with bind_phase_deadline(600):
        for s in seconds:
            observe(agent, s)


# --------------------------------------------------------------------------- #
# no phase's budget is a bare literal
# --------------------------------------------------------------------------- #

def test_the_budget_follows_the_slowest_measured_call():
    _seen("ScopeAgent", 51.0, 216.8, 100.5)
    assert phase_timeout("ScopeAgent") == int(216.8 * CALLS_PER_PHASE)


def test_the_budget_funds_more_than_one_call():
    """A budget of one call reduces fix 18's round ceiling to one by arithmetic."""
    _seen("DataAuditor", 200.0)
    assert phase_timeout("DataAuditor") >= 200.0 * 2


def test_no_phase_runner_still_passes_a_literal():
    """Acceptance: the 120 s / 180 s / 300 s literals are gone from the runners."""
    from pathlib import Path
    runners = Path("aaa/agents/tier1/phases/phase_runners")
    offenders = [
        f"{p.name}:{n}" for p in sorted(runners.glob("*.py"))
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if "timeout=" in line and any(c.isdigit() for c in line.split("timeout=")[1][:4])
    ]
    assert not offenders, f"phase budget literals still present: {offenders}"


# --------------------------------------------------------------------------- #
# a first call still has a defensible budget
# --------------------------------------------------------------------------- #

def test_a_cold_start_gets_the_floor():
    """Phase 1 always runs before anything is measured — and was lost 4 of 5 times."""
    assert phase_timeout("ScopeAgent") == int(MIN_PHASE_SECONDS)


def test_the_floor_covers_every_phase_1_call_the_run_made():
    """The worst was 216.8 s, against the 120 s budget that discarded it."""
    assert MIN_PHASE_SECONDS > 216.8


def test_an_agent_with_no_history_uses_what_its_peers_measured():
    # DataAuditor, not ModelValidator: the latter now has its own floor, which
    # would mask the pooled estimate this test is about.
    _seen("ScopeAgent", 216.8)
    assert phase_timeout("DataAuditor") == int(216.8 * CALLS_PER_PHASE)


def test_an_agent_with_its_own_history_prefers_it():
    """Payload size differs sharply by phase; the agent's own reading wins."""
    _seen("ScopeAgent", 216.8)
    _seen("DataAuditor", 39.0)
    assert phase_timeout("DataAuditor") == int(MIN_PHASE_SECONDS)


# --------------------------------------------------------------------------- #
# the clamps
# --------------------------------------------------------------------------- #

def test_a_fast_provider_cannot_push_the_budget_below_the_floor():
    _seen("DataAuditor", 39.0, 47.9)
    assert phase_timeout("DataAuditor") == int(MIN_PHASE_SECONDS)


def test_a_pathological_call_cannot_run_away():
    _seen("DataAuditor", 5000.0)
    assert phase_timeout("DataAuditor") == int(MAX_PHASE_SECONDS)


def test_the_ceiling_still_funds_two_of_the_slowest_call_ever_measured():
    """347.8 s, case 03 #040 — and it delivered 11,480 characters."""
    assert MAX_PHASE_SECONDS >= 347.8 * CALLS_PER_PHASE


# --------------------------------------------------------------------------- #
# what gets measured
# --------------------------------------------------------------------------- #

def test_a_call_outside_a_phase_deadline_is_not_a_phase_measurement():
    """The Verifier and the Orchestrator run outside any phase timeout."""
    observe("Verifier", 319.7)
    observe("Orchestrator", 303.7)
    assert slowest_call() is None
    assert phase_timeout("ScopeAgent") == int(MIN_PHASE_SECONDS)


def test_a_non_positive_duration_says_nothing_and_is_ignored():
    _seen("ScopeAgent", 0.0, -1.0)
    assert slowest_call("ScopeAgent") is None


def test_one_outlier_ages_out_of_the_window():
    """A 347.8 s call must not pin every later phase to a 695 s wait all run."""
    _seen("DataAuditor", 347.8)
    assert phase_timeout("DataAuditor") == int(347.8 * CALLS_PER_PHASE)
    _seen("DataAuditor", *[60.0] * WINDOW)
    assert phase_timeout("DataAuditor") == int(MIN_PHASE_SECONDS)


# --------------------------------------------------------------------------- #
# fix 18's clock gates are calibrated against this budget, so they move with it
# --------------------------------------------------------------------------- #

def test_the_round_the_old_budget_refused_now_fits():
    """Fix 18's own worked example, re-asked against a budget that is measured.

    `rounds.py` records it: Phase 3's rerun *"would have declined its one round
    (71 s left, 106.3 s last call)"*. Under 180 s that was the right call and the
    phase answered on its seed. The gate is unchanged; the room it measures is
    not.
    """
    import time
    from unittest.mock import patch

    from aaa.tools.evidence_retrieval.rounds import rounds_fit

    _seen("DataAuditor", 106.3)
    budget = phase_timeout("DataAuditor")
    assert budget >= 300

    started = time.monotonic()
    with bind_phase_deadline(budget):
        # stand 106.3 s into the phase, exactly where the gate was asked
        with patch("aaa.platform.phase_budget.deadline.time.monotonic",
                   return_value=started + 106.3):
            assert rounds_fit([106.3], 1) is True


def test_the_gate_still_refuses_a_round_that_genuinely_will_not_fit():
    """A bigger budget is not a disabled gate."""
    import time
    from unittest.mock import patch

    from aaa.tools.evidence_retrieval.rounds import rounds_fit

    started = time.monotonic()
    with bind_phase_deadline(300):
        with patch("aaa.platform.phase_budget.deadline.time.monotonic",
                   return_value=started + 250.0):
            assert rounds_fit([106.3], 1) is False
