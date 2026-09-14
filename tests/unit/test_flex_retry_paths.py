"""flex_acompletion happy paths: standard tier and first-attempt Flex."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aaa.platform.flex_retry import DEFAULT_TIMEOUT_SECONDS, FLEX_TIMEOUT_SECONDS
from tests.unit.support.flex_retry_helpers import flex_module, ok_response


@pytest.mark.asyncio
async def test_non_flex_single_attempt():
    """Standard-tier calls go through in one attempt with the default timeout."""
    fake_resp = ok_response()
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=fake_resp)

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await flex_module().flex_acompletion(model="gpt-5.4", messages=[])

    mock_litellm.acompletion.assert_called_once()
    call_kwargs = mock_litellm.acompletion.call_args.kwargs
    assert call_kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS
    assert "service_tier" not in call_kwargs
    assert result is fake_resp


@pytest.mark.asyncio
async def test_flex_success_first_attempt():
    """Flex call succeeds immediately — no retries, uses flex timeout."""
    fake_resp = ok_response()
    mock_litellm = MagicMock()
    mock_litellm.acompletion = AsyncMock(return_value=fake_resp)

    with patch.dict("sys.modules", {"litellm": mock_litellm}):
        result = await flex_module().flex_acompletion(
            model="gpt-5.5", service_tier="flex", messages=[])

    assert result is fake_resp
    call_kwargs = mock_litellm.acompletion.call_args.kwargs
    assert call_kwargs["timeout"] == FLEX_TIMEOUT_SECONDS
    assert call_kwargs["service_tier"] == "flex"
