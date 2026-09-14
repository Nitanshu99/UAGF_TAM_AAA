"""flex_acompletion failure modes: exhausted retries and non-retryable errors."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.unit.support.flex_retry_helpers import flex_module, rate_limit_exc, retry_module


@pytest.mark.asyncio
async def test_flex_raises_runtime_error_when_fallback_also_fails(monkeypatch):
    """RuntimeError is raised when both Flex and standard-tier fallback fail."""
    async def _always_fail(**kwargs):
        raise rate_limit_exc()

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _always_fail
    module = flex_module()
    monkeypatch.setattr(retry_module().asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        with pytest.raises(RuntimeError, match="Flex retries exhausted"):
            await module.flex_acompletion(
                model="gpt-5.5", service_tier="flex", messages=[])


@pytest.mark.asyncio
async def test_non_retryable_error_propagates_immediately(monkeypatch):
    """A non-429 error (e.g. auth failure) is not retried — it re-raises at once."""
    call_count = {"n": 0}

    async def _auth_fail(**kwargs):
        call_count["n"] += 1
        raise PermissionError("401 Invalid API key")

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _auth_fail
    module = flex_module()
    monkeypatch.setattr(retry_module().asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        with pytest.raises(PermissionError):
            await module.flex_acompletion(
                model="gpt-5.5", service_tier="flex", messages=[])

    # Only one attempt — no retries for non-rate-limit errors.
    assert call_count["n"] == 1
