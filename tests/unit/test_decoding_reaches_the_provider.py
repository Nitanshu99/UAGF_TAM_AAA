"""The decoding policy reaches the provider on every attempt of every call.

``_acompletion_once`` is the one place every agent call passes through, so it is
where the policy is merged — before the Flex ladder's retry and standard-tier
fallback copy the arguments. Driven through the real function with litellm
replaced by a recorder (T-20260913-002).
"""
from __future__ import annotations

import pytest

from aaa.platform.model_registry.decoding import DEFAULT_SEED
from tests.unit.support.flex_retry_helpers import capture_call_kwargs


@pytest.mark.asyncio
async def test_every_call_carries_the_decoding_parameters(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The point of the fix: the provider is told to decode greedily."""
    monkeypatch.delenv("AAA_LLM_TEMPERATURE", raising=False)
    monkeypatch.delenv("AAA_LLM_SEED", raising=False)
    seen = await capture_call_kwargs(monkeypatch)
    assert seen["temperature"] == 0.0
    assert seen["seed"] == DEFAULT_SEED


@pytest.mark.asyncio
async def test_a_caller_can_still_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """The escape hatch is real — an explicit value is not overwritten."""
    seen = await capture_call_kwargs(monkeypatch, temperature=0.9)
    assert seen["temperature"] == 0.9


@pytest.mark.asyncio
async def test_an_unsupported_parameter_does_not_fail_the_call(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """GPT-5-family models refuse ``temperature=0``; the call must still go out.

    Scoped to the call rather than litellm's global flag, so nothing else in the
    process changes behaviour.
    """
    seen = await capture_call_kwargs(monkeypatch)
    assert seen["drop_params"] is True
    assert seen["_global_drop_params"] is False


@pytest.mark.asyncio
async def test_a_reasoning_model_call_carries_no_temperature(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The call path honours the rule, so the default roster is not refused.

    The capability check is pinned here because the recorder stands in for
    litellm; it is tested against the real litellm in ``test_decoding_is_recorded``.
    """
    from aaa.platform.model_registry.decoding import policy

    monkeypatch.setattr(policy, "refuses_temperature", lambda model: model == "gpt-5.6-terra")
    seen = await capture_call_kwargs(monkeypatch, model="gpt-5.6-terra")
    assert "temperature" not in seen
    assert seen["seed"] == DEFAULT_SEED
