"""Shared fakes for the flex_retry tests (no network traffic)."""
from __future__ import annotations

import importlib
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


def ok_response() -> MagicMock:
    """Minimal fake litellm response object."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = '{"verdict": "PASS"}'
    return resp


def rate_limit_exc(msg: str = "429 Resource Unavailable") -> RuntimeError:
    """A rate-limit-shaped exception."""
    return RuntimeError(msg)


def flex_module() -> Any:
    """The module holding the ``flex_acompletion`` entry point."""
    return importlib.import_module("aaa.platform.flex_retry.flex_acompletion")


def retry_module() -> Any:
    """The module holding the Flex ladder — ``asyncio.sleep`` lives here."""
    return importlib.import_module("aaa.platform.flex_retry.ladder")


def call_module() -> Any:
    """The module holding the single call — ``litellm`` is imported here."""
    return importlib.import_module("aaa.platform.flex_retry.one_call")


async def capture_call_kwargs(monkeypatch: pytest.MonkeyPatch, model: str = "m",
                              **call: Any) -> dict[str, Any]:
    """Run one call through the real ``_acompletion_once``; return what litellm was sent.

    litellm is replaced by a recorder whose own ``drop_params`` flag starts
    ``False``, so a test can also tell whether the call touched the global.
    """
    seen: dict[str, Any] = {}

    class _RecordingLiteLLM:
        drop_params = False

        @staticmethod
        async def acompletion(**kwargs: Any) -> Any:
            """Record what the provider was sent."""
            seen.update(kwargs)
            return object()

    monkeypatch.setitem(sys.modules, "litellm", _RecordingLiteLLM)
    monkeypatch.setattr(call_module(), "acquire_for_model", AsyncMock(), raising=False)
    await call_module()._acompletion_once(model=model, messages=[], **call)
    seen["_global_drop_params"] = _RecordingLiteLLM.drop_params
    return seen
