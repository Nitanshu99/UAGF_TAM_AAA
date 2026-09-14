"""Unit tests for the flex_retry helper predicates."""
from __future__ import annotations

from aaa.platform.flex_retry import _is_rate_limit, _strip_flex


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
