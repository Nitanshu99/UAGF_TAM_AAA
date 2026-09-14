"""Timeout ceilings must be overridable, and must never fail closed on junk."""
from __future__ import annotations

import pytest

from aaa.platform.flex_retry.logger import _timeout


def test_unset_uses_default(monkeypatch):
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)
    assert _timeout("LLM_TIMEOUT_SECONDS", 120.0) == 120.0


@pytest.mark.parametrize("raw,expected", [
    ("600", 600.0),
    ("90.5", 90.5),
])
def test_override_is_applied(monkeypatch, raw, expected):
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", raw)
    assert _timeout("LLM_TIMEOUT_SECONDS", 120.0) == expected


@pytest.mark.parametrize("raw", ["", "abc", "2 minutes"])
def test_unparseable_falls_back_to_default(monkeypatch, raw):
    """A typo must not silently become a zero-second timeout."""
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", raw)
    assert _timeout("LLM_TIMEOUT_SECONDS", 120.0) == 120.0
