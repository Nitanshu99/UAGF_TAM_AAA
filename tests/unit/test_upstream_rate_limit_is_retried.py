"""An upstream provider's temporary 429 is transient; a spent quota is not (T-20260914-048)."""
from __future__ import annotations

from aaa.platform.transient_retry.classify import is_transient


class RateLimitError(Exception):
    """Stands in for ``litellm.RateLimitError`` — only its type name is read."""


def test_the_case_03_upstream_saturation_is_retried() -> None:
    """2026-09-14 11:30: every call made one attempt and the run was unclean."""
    message = ('litellm.RateLimitError: RateLimitError: OpenrouterException - {"error":{"message":'
               '"Provider returned error","code":429,"metadata":{"raw":"minimax/minimax-m3 is '
               'temporarily rate-limited upstream. Please retry shortly"}}}')
    assert is_transient(RateLimitError(message))


def test_a_spent_quota_or_a_plain_rate_limit_stays_terminal() -> None:
    """Waiting seconds does not restore a daily limit, and our own pacing owns the rest."""
    assert not is_transient(RateLimitError("429 Rate limit exceeded: free-models-per-day"))
    assert not is_transient(RateLimitError("429 temporarily rate-limited: insufficient credits"))
    assert not is_transient(RateLimitError("429 Too Many Requests"))


def test_an_upstream_rate_limit_waits_out_a_two_minute_saturation() -> None:
    """Case 03 w1a2: ~18 s of retries did not outlast a one-to-two-minute window."""
    from aaa.platform.transient_retry.backoff import MAX_RATE_LIMIT_RETRIES, backoff_seconds

    floor = sum(backoff_seconds(n, draw=lambda: 0.0, rate_limited=True)
                for n in range(MAX_RATE_LIMIT_RETRIES))
    assert floor >= 120
    assert backoff_seconds(0, draw=lambda: 0.0) == 1.0  # the transient schedule is unchanged


def test_the_ladder_keeps_retrying_an_upstream_rate_limit(monkeypatch) -> None:
    """More attempts than the transient schedule allows, then success."""
    import asyncio

    from aaa.platform.transient_retry import ladder as ladder_module

    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(ladder_module.asyncio, "sleep", _no_sleep)
    calls: list[int] = []

    async def _call(**_kwargs):
        calls.append(1)
        if len(calls) <= 6:
            raise RateLimitError("minimax/minimax-m3 is temporarily rate-limited upstream")
        return "ok"

    value, failure, _elapsed, _stopped = asyncio.run(ladder_module.ladder(_call, {"model": "m"}))
    assert (value, failure, len(calls)) == ("ok", None, 7)
