"""Unit tests for the S6/S7 provider settings (defaults + env override)."""
from __future__ import annotations

from aaa.settings import AAASettings


def _cfg() -> dict:
    """Instantiate settings without the repo .env and dump to a plain dict."""
    cfg = AAASettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    return cfg.model_dump()


def test_defaults_are_internal(monkeypatch) -> None:
    """Both providers default to internal mode with local base URLs."""
    for var in ("S6_XAI_MODE", "S6_XAI_BASE_URL", "S7_SEC_MODE"):
        monkeypatch.delenv(var, raising=False)
    cfg = _cfg()
    assert cfg["s6_xai_mode"] == "internal"
    assert cfg["s7_sec_mode"] == "internal"
    assert cfg["s6_xai_base_url"] == "http://localhost:8006"
    assert cfg["s7_sec_base_url"] == "http://localhost:8007"


def test_env_overrides_independently(monkeypatch) -> None:
    """S6 can flip to external while S7 stays internal (and vice versa)."""
    monkeypatch.setenv("S6_XAI_MODE", "external")
    monkeypatch.setenv("S6_XAI_BASE_URL", "http://s6.example:9000")
    cfg = _cfg()
    assert cfg["s6_xai_mode"] == "external"
    assert cfg["s6_xai_base_url"] == "http://s6.example:9000"
    assert cfg["s7_sec_mode"] == "internal"


def test_safe_repr_exposes_modes_not_tokens() -> None:
    """safe_repr surfaces the modes/URLs but never bearer tokens."""
    instance = AAASettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    safe = instance.safe_repr()
    assert safe["s6_xai_mode"] and safe["s7_sec_base_url"]
    assert not any("token" in key or "key" in key for key in safe)
