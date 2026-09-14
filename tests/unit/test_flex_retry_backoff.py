"""flex_acompletion retry-and-fallback behaviour on 429s."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aaa.platform.flex_retry import FLEX_MAX_RETRIES
from tests.unit.support.flex_retry_helpers import (
    flex_module,
    ok_response,
    rate_limit_exc,
    retry_module,
)


@pytest.mark.asyncio
async def test_flex_retries_on_429_then_succeeds(monkeypatch):
    """Flex path retries on 429 and succeeds on the third attempt."""
    fake_resp = ok_response()
    calls = {"n": 0}

    async def _flaky(**kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise rate_limit_exc()
        return fake_resp

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _flaky
    module = flex_module()
    monkeypatch.setattr(retry_module().asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await module.flex_acompletion(
            model="gpt-5.5", service_tier="flex", messages=[])

    assert result is fake_resp
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_flex_falls_back_to_standard_after_max_retries(monkeypatch):
    """After FLEX_MAX_RETRIES Flex failures, one standard-tier attempt is made."""
    fake_resp = ok_response()
    flex_calls = {"n": 0}
    standard_calls = {"n": 0}

    async def _sideeffect(**kwargs):
        if kwargs.get("service_tier") == "flex":
            flex_calls["n"] += 1
            raise rate_limit_exc()
        standard_calls["n"] += 1
        return fake_resp

    mock_litellm = MagicMock()
    mock_litellm.acompletion = _sideeffect
    module = flex_module()
    monkeypatch.setattr(retry_module().asyncio, "sleep", AsyncMock())

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await module.flex_acompletion(
            model="gpt-5.5", service_tier="flex", messages=[])

    assert flex_calls["n"] == FLEX_MAX_RETRIES
    assert standard_calls["n"] == 1
    assert result is fake_resp
