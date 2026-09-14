"""Fix 46 — the ceiling bounds what its name says (finding R14).

Case 04 call #024 ran **319.7 s against a 300 s ceiling and returned `ok`**. The
mechanism, established from the code rather than inferred from the latency:

* `openai/_base_client.py` loops `for retries_taken in range(max_retries + 1)`
  and builds the request **inside** that loop, so `timeout` bounds one attempt;
* `litellm/llms/openai/openai.py` passes `max_retries` straight to `AsyncOpenAI`,
  defaulted to `DEFAULT_MAX_RETRIES` — 2 in both packages.

A ceiling of N seconds therefore bounded up to 3N of wall-clock, while
`latency_ms` recorded the whole sequence. The two were never commensurable.
"""
from __future__ import annotations

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aaa.platform.flex_retry import CLIENT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS
from aaa.platform.model_registry.timeouts import VERIFIER_TIMEOUT_SECONDS
from aaa.platform.phase_budget import bind_phase_deadline
from tests.unit.support.flex_retry_helpers import flex_module, ok_response, retry_module

# --------------------------------------------------------------------------- #
# the mechanism, asserted against the installed packages
# --------------------------------------------------------------------------- #

def test_the_client_beneath_us_defaults_to_retrying():
    """If this ever stops being true, the reasoning below needs revisiting."""
    import openai
    assert openai._constants.DEFAULT_MAX_RETRIES == 2


def test_the_client_applies_its_timeout_per_attempt():
    """The request is built *inside* the retry loop, so each attempt gets it."""
    from openai import _base_client

    source = inspect.getsource(_base_client)
    assert "for retries_taken in range(max_retries + 1):" in source


def test_litellm_passes_max_retries_to_the_client():
    from litellm.llms.openai import openai as litellm_openai

    source = inspect.getsource(litellm_openai)
    assert "max_retries=max_retries" in source


# --------------------------------------------------------------------------- #
# so we pin it, and the ceiling bounds the call
# --------------------------------------------------------------------------- #

def test_we_leave_the_client_no_retries_of_its_own():
    assert CLIENT_MAX_RETRIES == 0


@pytest.mark.asyncio
async def test_every_call_pins_the_client_retries():
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=ok_response())
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        await flex_module().flex_acompletion(model="m", messages=[])
    assert mock_litellm.acompletion.call_args.kwargs["max_retries"] == 0


@pytest.mark.asyncio
async def test_a_caller_that_wants_client_retries_may_still_ask():
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=ok_response())
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        await flex_module().flex_acompletion(model="m", messages=[], max_retries=3)
    assert mock_litellm.acompletion.call_args.kwargs["max_retries"] == 3


@pytest.mark.asyncio
async def test_the_flex_fallback_pins_them_too():
    """The standard-tier fallback is a second call site and had to be covered."""
    from tests.unit.support.flex_retry_helpers import rate_limit_exc

    calls: list[dict] = []

    async def _fail_then_ok(**kwargs):
        calls.append(kwargs)
        if kwargs.get("service_tier") == "flex":
            raise rate_limit_exc()
        return ok_response()

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _fail_then_ok
    module = flex_module()
    with patch.object(retry_module().asyncio, "sleep", AsyncMock()):
        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            await module.flex_acompletion(model="m", service_tier="flex", messages=[])
    assert calls[-1]["max_retries"] == 0
    assert "service_tier" not in calls[-1]


# --------------------------------------------------------------------------- #
# a call that exceeds the ceiling is actually cut off
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_a_call_past_the_ceiling_is_cut_off():
    """With no client retries, one attempt's timeout is the call's timeout."""
    passed: dict = {}

    async def _slow(**kwargs):
        passed.update(kwargs)
        # The real client raises APITimeoutError here once `timeout` elapses; with
        # max_retries=0 there is no second attempt to hide behind.
        raise TimeoutError(f"timed out after {kwargs['timeout']}s")

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _slow
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        with pytest.raises(TimeoutError):
            await flex_module().flex_acompletion(model="m", messages=[])
    assert passed["timeout"] == DEFAULT_TIMEOUT_SECONDS
    assert passed["max_retries"] == 0


def test_the_ceiling_and_the_recorded_latency_now_measure_the_same_thing():
    """`latency_ms` spans the whole call; with no hidden retries, so does the ceiling."""
    async def _run():
        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(return_value=ok_response())
        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            with bind_phase_deadline(VERIFIER_TIMEOUT_SECONDS):
                await flex_module().flex_acompletion(model="m", messages=[])
        kwargs = mock_litellm.acompletion.call_args.kwargs
        # one attempt, so the wall-clock bound is the number itself, not 3x it
        return kwargs["timeout"] * (kwargs["max_retries"] + 1)

    assert asyncio.run(_run()) <= VERIFIER_TIMEOUT_SECONDS


# --------------------------------------------------------------------------- #
# a bound that binds for the first time has to be sized against what it cuts off
# --------------------------------------------------------------------------- #

def test_the_verifier_ceiling_sits_above_the_slowest_call_that_came_back():
    """Fix 20's rule, re-applied to the data that moved its premise.

    Fix 20 chose 300 s as the smallest round value above 240.3 s. This run's
    slowest *successful* Verifier call was 319.7 s — case 04 #024, the very call
    finding R14 is about — and a ceiling that now binds would have cut it off.
    """
    slowest_that_returned = 319.7
    assert VERIFIER_TIMEOUT_SECONDS > slowest_that_returned
    assert VERIFIER_TIMEOUT_SECONDS == 360.0


def test_the_verifier_ceiling_is_no_longer_tripled_underneath():
    effective = VERIFIER_TIMEOUT_SECONDS * (CLIENT_MAX_RETRIES + 1)
    assert effective == VERIFIER_TIMEOUT_SECONDS
    assert effective < VERIFIER_TIMEOUT_SECONDS * 3, "the old effective bound"
