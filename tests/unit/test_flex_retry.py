"""
Unit tests for aaa.platform.flex_retry.

All LiteLLM calls are mocked so no network traffic is generated.
asyncio.sleep is also patched to keep tests fast.
"""
from __future__ import annotations

import asyncio
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aaa.platform.flex_retry import (
    DEFAULT_TIMEOUT_SECONDS,
    FLEX_BACKOFF_BASE,
    FLEX_MAX_RETRIES,
    FLEX_TIMEOUT_SECONDS,
    _is_rate_limit,
    _strip_flex,
    flex_acompletion,
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _ok_response():
    """Minimal fake litellm response object."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = '{"verdict": "PASS"}'
    return resp


def _rate_limit_exc(msg: str = "429 Resource Unavailable"):
    return RuntimeError(msg)


# ---------------------------------------------------------------------------
# _is_rate_limit
# ---------------------------------------------------------------------------

class TestIsRateLimit:
    def test_detects_429_in_message(self):
        assert _is_rate_limit(RuntimeError("429 too many requests")) is True

    def test_detects_rate_limit_in_message(self):
        assert _is_rate_limit(Exception("rate limit exceeded")) is True

    def test_detects_resource_unavailable(self):
        assert _is_rate_limit(Exception("Resource Unavailable")) is True

    def test_detects_RateLimitError_type_name(self):
        class RateLimitError(Exception):
            pass
        assert _is_rate_limit(RateLimitError("boom")) is True

    def test_ignores_unrelated_error(self):
        assert _is_rate_limit(ValueError("bad input")) is False

    def test_ignores_auth_error(self):
        assert _is_rate_limit(PermissionError("401 Unauthorized")) is False


# ---------------------------------------------------------------------------
# _strip_flex
# ---------------------------------------------------------------------------

class TestStripFlex:
    def test_removes_service_tier(self):
        out = _strip_flex({"model": "gpt-5.5", "service_tier": "flex"})
        assert "service_tier" not in out
        assert out["model"] == "gpt-5.5"

    def test_leaves_other_kwargs_intact(self):
        out = _strip_flex({"model": "m", "service_tier": "flex", "timeout": 60})
        assert out["timeout"] == 60

    def test_noop_when_no_service_tier(self):
        kw = {"model": "m", "messages": []}
        assert _strip_flex(kw) == kw

    def test_does_not_mutate_original(self):
        kw = {"model": "m", "service_tier": "flex"}
        _strip_flex(kw)
        assert kw["service_tier"] == "flex"


# ---------------------------------------------------------------------------
# flex_acompletion — non-Flex path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_non_flex_single_attempt():
    """Standard-tier calls go through in one attempt with the default timeout."""
    fake_resp = _ok_response()
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=fake_resp)

    import aaa.platform.flex_retry as module
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await module.flex_acompletion(model="gpt-5.4", messages=[])

    mock_litellm.acompletion.assert_called_once()
    call_kwargs = mock_litellm.acompletion.call_args.kwargs
    assert call_kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS
    assert "service_tier" not in call_kwargs
    assert result is fake_resp


@pytest.mark.asyncio
async def test_flex_success_first_attempt():
    """Flex call succeeds immediately — no retries, uses flex timeout."""
    fake_resp = _ok_response()
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=fake_resp)

    import aaa.platform.flex_retry as module
    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await module.flex_acompletion(
            model="gpt-5.5", service_tier="flex", messages=[]
        )

    assert result is fake_resp
    call_kwargs = mock_litellm.acompletion.call_args.kwargs
    assert call_kwargs["timeout"] == FLEX_TIMEOUT_SECONDS
    assert call_kwargs["service_tier"] == "flex"


@pytest.mark.asyncio
async def test_flex_retries_on_429_then_succeeds(monkeypatch):
    """Flex path retries on 429 and succeeds on the third attempt."""
    fake_resp = _ok_response()
    calls = {"n": 0}

    async def _flaky(**kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise _rate_limit_exc()
        return fake_resp

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _flaky

    import aaa.platform.flex_retry as module
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await module.flex_acompletion(
            model="gpt-5.5", service_tier="flex", messages=[]
        )

    assert result is fake_resp
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_flex_falls_back_to_standard_after_max_retries(monkeypatch):
    """After FLEX_MAX_RETRIES Flex failures, one standard-tier attempt is made."""
    fake_resp = _ok_response()
    flex_calls = {"n": 0}
    standard_calls = {"n": 0}

    async def _sideeffect(**kwargs):
        if kwargs.get("service_tier") == "flex":
            flex_calls["n"] += 1
            raise _rate_limit_exc()
        else:
            standard_calls["n"] += 1
            return fake_resp

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _sideeffect

    import aaa.platform.flex_retry as module
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await module.flex_acompletion(
            model="gpt-5.5", service_tier="flex", messages=[]
        )

    assert flex_calls["n"] == FLEX_MAX_RETRIES
    assert standard_calls["n"] == 1
    assert result is fake_resp


@pytest.mark.asyncio
async def test_flex_raises_runtime_error_when_fallback_also_fails(monkeypatch):
    """RuntimeError is raised when both Flex and standard-tier fallback fail."""

    async def _always_fail(**kwargs):
        raise _rate_limit_exc()

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _always_fail

    import aaa.platform.flex_retry as module
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        with pytest.raises(RuntimeError, match="Flex retries exhausted"):
            await module.flex_acompletion(
                model="gpt-5.5", service_tier="flex", messages=[]
            )


@pytest.mark.asyncio
async def test_non_retryable_error_propagates_immediately(monkeypatch):
    """A non-429 error (e.g. auth failure) is not retried — it re-raises at once."""
    call_count = {"n": 0}

    async def _auth_fail(**kwargs):
        call_count["n"] += 1
        raise PermissionError("401 Invalid API key")

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _auth_fail

    import aaa.platform.flex_retry as module
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        with pytest.raises(PermissionError):
            await module.flex_acompletion(
                model="gpt-5.5", service_tier="flex", messages=[]
            )

    # Only one attempt — no retries for non-rate-limit errors.
    assert call_count["n"] == 1
