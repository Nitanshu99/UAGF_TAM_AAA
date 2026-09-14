"""acquire_for_model: routes nvidia_nim/* calls through the shared limiter."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from aaa.platform.rate_limit import acquire_for_model


@pytest.mark.asyncio
async def test_acquire_for_model_noop_for_non_nvidia(monkeypatch):
    """Non-NVIDIA model strings never touch the shared limiter."""
    called = AsyncMock()
    monkeypatch.setattr("aaa.platform.rate_limit._nvidia_limiter.acquire", called)

    await acquire_for_model("gpt-5.6-terra")

    called.assert_not_awaited()


@pytest.mark.asyncio
async def test_acquire_for_model_throttles_nvidia_nim(monkeypatch):
    """nvidia_nim/-prefixed models go through the shared limiter."""
    called = AsyncMock()
    monkeypatch.setattr("aaa.platform.rate_limit._nvidia_limiter.acquire", called)

    await acquire_for_model("nvidia_nim/nvidia/nemotron-3-nano-30b-a3b")

    called.assert_awaited_once()
