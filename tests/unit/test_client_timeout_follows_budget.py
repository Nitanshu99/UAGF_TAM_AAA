"""Fix 37 — one number, two consumers (finding R6).

The ReportArchitect was given a 180 s phase budget and a 120 s client ceiling, so
Phase 6 was structurally unable to use the time it was allocated. It failed
identically in two cases, 187.0 s against `timeout value=120.0`. Fix 34 then made
the gap wider, not narrower: a derived budget of 300–695 s over a ceiling still
fixed at 120 s.
"""
from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aaa.platform.flex_retry import DEFAULT_TIMEOUT_SECONDS, FLEX_TIMEOUT_SECONDS
from aaa.platform.model_registry.timeouts import VERIFIER_TIMEOUT_SECONDS, resolve_client_timeout
from aaa.platform.phase_budget import bind_phase_deadline, phase_timeout
from tests.unit.support.flex_retry_helpers import flex_module, ok_response

#: The two calls the run lost to this defect, and what they actually took.
LOST = {"case 01 #044": 186.98, "case 03 #045": 186.99}


# --------------------------------------------------------------------------- #
# inside a phase, the ceiling is the budget
# --------------------------------------------------------------------------- #

def test_inside_a_phase_the_ceiling_is_what_the_phase_has_left():
    with bind_phase_deadline(300):
        left = resolve_client_timeout(None, DEFAULT_TIMEOUT_SECONDS)
    assert 299.0 < left <= 300.0


def test_the_ceiling_can_no_longer_be_lower_than_the_budget_it_sits_inside():
    """The acceptance criterion, stated as an assertion."""
    for budget in (180, 300, 511, 695):
        with bind_phase_deadline(budget):
            assert resolve_client_timeout(None, DEFAULT_TIMEOUT_SECONDS) > budget - 1


@pytest.mark.parametrize("call,elapsed", sorted(LOST.items()))
def test_both_calls_the_run_lost_would_now_have_completed(call, elapsed):
    """Phase 6's derived budget, against the latency that actually came back."""
    budget = phase_timeout("ReportArchitect")          # cold start: the 300 s floor
    with bind_phase_deadline(budget):
        assert resolve_client_timeout(None, DEFAULT_TIMEOUT_SECONDS) > elapsed


def test_a_spent_budget_falls_back_rather_than_passing_a_negative_ceiling():
    started = time.monotonic()
    with bind_phase_deadline(10):
        with patch("aaa.platform.phase_budget.deadline.time.monotonic",
                   return_value=started + 60):
            assert resolve_client_timeout(None, DEFAULT_TIMEOUT_SECONDS) == \
                DEFAULT_TIMEOUT_SECONDS


# --------------------------------------------------------------------------- #
# outside a phase, nothing changed — which is what preserves fix 20
# --------------------------------------------------------------------------- #

def test_the_verifiers_own_ceiling_is_untouched():
    """It runs after `run_agent_on_state` returns, so it binds no deadline.

    The *value* moved under fix 46 — 300 s never bound anything, and re-applying
    fix 20's own rule to the run that made it bind gives 360 s. What this test
    asserts is that fix 37 does not touch it, whatever it is.
    """
    assert resolve_client_timeout(VERIFIER_TIMEOUT_SECONDS,
                                  DEFAULT_TIMEOUT_SECONDS) == VERIFIER_TIMEOUT_SECONDS
    assert VERIFIER_TIMEOUT_SECONDS == 360.0


def test_a_caller_with_no_ceiling_outside_a_phase_takes_the_default():
    assert resolve_client_timeout(None, DEFAULT_TIMEOUT_SECONDS) == DEFAULT_TIMEOUT_SECONDS


# --------------------------------------------------------------------------- #
# and the number actually reaches litellm
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_the_budget_is_the_timeout_litellm_is_given():
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=ok_response())
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        with bind_phase_deadline(511):
            await flex_module().flex_acompletion(model="m", messages=[])
    passed = mock_litellm.acompletion.call_args.kwargs["timeout"]
    assert 510.0 < passed <= 511.0


@pytest.mark.asyncio
async def test_a_call_outside_a_phase_still_gets_the_platform_default():
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=ok_response())
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        await flex_module().flex_acompletion(model="m", messages=[])
    assert mock_litellm.acompletion.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS


@pytest.mark.asyncio
async def test_the_flex_default_is_still_reachable():
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=ok_response())
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        await flex_module().flex_acompletion(model="m", service_tier="flex", messages=[])
    assert mock_litellm.acompletion.call_args.kwargs["timeout"] == FLEX_TIMEOUT_SECONDS


# --------------------------------------------------------------------------- #
# the two cannot drift apart again
# --------------------------------------------------------------------------- #

def test_only_agents_that_can_run_without_a_phase_declare_a_ceiling_of_their_own():
    """A second constant beside the budget is how R6 happened.

    The Verifier runs after `run_agent_on_state` returns and the Orchestrator's
    decide loop runs outside phases altogether, so neither has a budget to read.
    ClientBrief is the first agent on *both* sides: dispatched through a phase in
    a pipeline run, and dispatched through nothing at all when a saved state is
    rewritten by `python -m aaa brief`. Its entry is for the second path only —
    which the next assertion, not this list, is what actually holds.

    An agent that can *only* run inside a phase still must not appear here.
    """
    from aaa.platform.model_registry.timeouts import AGENT_TIMEOUTS
    assert set(AGENT_TIMEOUTS) == {"Verifier", "Orchestrator", "ClientBrief"}, (
        "an agent that runs inside a phase must take its ceiling from the budget, "
        "not declare a second one beside it")


@pytest.mark.parametrize("agent_name", ["Verifier", "Orchestrator", "ClientBrief"])
def test_no_declared_ceiling_can_outrank_a_phase_budget(agent_name):
    """The R6 invariant, asserted against every agent that declares a ceiling.

    This is what makes the list above safe to extend: whatever an agent declares,
    a bound deadline wins, so a ceiling can never again sit *under* the budget it
    runs inside — nor over it.
    """
    from aaa.platform.model_registry.timeouts import AGENT_TIMEOUTS
    with bind_phase_deadline(90):
        left = resolve_client_timeout(AGENT_TIMEOUTS[agent_name],
                                      DEFAULT_TIMEOUT_SECONDS)
    assert 89.0 < left <= 90.0


def test_the_ceiling_is_read_not_declared():
    """Structural: the ceiling is resolved, never taken straight from a constant."""
    from pathlib import Path
    src = Path("aaa/platform/flex_retry/one_call.py").read_text()
    assert 'timeout = resolve_client_timeout(kwargs.get("timeout"), default)' in src
    assert 'timeout = kwargs.get("timeout") or default' not in src


# --------------------------------------------------------------------------- #
# the Orchestrator: the one place fix 46 could have bitten
# --------------------------------------------------------------------------- #

def test_the_orchestrators_ceiling_sits_above_its_slowest_returning_call():
    """Its calls ran to 303.7 s under a nominal 120 s, which only fix 46's
    tripling permitted. Fix 20's rule, applied to this agent's own data."""
    from aaa.platform.model_registry.timeouts import ORCHESTRATOR_TIMEOUT_SECONDS

    assert ORCHESTRATOR_TIMEOUT_SECONDS > 303.7
    assert ORCHESTRATOR_TIMEOUT_SECONDS == 360.0


def test_the_client_briefs_ceiling_sits_above_its_slowest_returning_call():
    """Fix 20's rule again, on the 2026-09-09 Mariposa brief.

    Nineteen calls: two cut off at ``timeout value=120.0`` (211.6 s and 312.2 s),
    both losing their section to the deterministic fallback, while the slowest
    call that *did* return took 385.8 s from the same provider in the same run.
    """
    from aaa.platform.model_registry.timeouts import CLIENT_BRIEF_TIMEOUT_SECONDS

    assert CLIENT_BRIEF_TIMEOUT_SECONDS > 385.8
    assert CLIENT_BRIEF_TIMEOUT_SECONDS == 420.0


def test_the_orchestrator_actually_takes_it():
    from aaa.agents.tier1.orchestrator.agent import Orchestrator
    from aaa.platform.model_registry.timeouts import ORCHESTRATOR_TIMEOUT_SECONDS

    orch = Orchestrator()
    assert orch.timeout == ORCHESTRATOR_TIMEOUT_SECONDS
    assert orch._litellm_kwargs()["timeout"] == ORCHESTRATOR_TIMEOUT_SECONDS


def test_a_phase_budget_still_wins_over_an_agents_own_ceiling():
    """Inside a phase there is a real deadline, and it is the authority."""
    from aaa.platform.model_registry.timeouts import ORCHESTRATOR_TIMEOUT_SECONDS

    with bind_phase_deadline(90):
        left = resolve_client_timeout(ORCHESTRATOR_TIMEOUT_SECONDS,
                                      DEFAULT_TIMEOUT_SECONDS)
    assert 89.0 < left <= 90.0
