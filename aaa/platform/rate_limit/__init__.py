"""rate_limit — throttle LLM calls against provider free-tier caps.

Covers NVIDIA NIM's 40-requests-per-minute free tier and OpenRouter's
20-per-minute cap on ``:free`` model routes. Any other model string is
untouched — OpenAI (GPT-5.6) calls never wait.

OpenRouter also publishes a *daily* cap on free routes: 50 requests on an
account that has never purchased credits, 1000 once $10 has been bought at any
point. That one is deliberately not implemented here. A limiter can smooth a
per-minute cap by waiting a few seconds; waiting out a daily quota would stall
an audit for hours, so exceeding it must surface as the provider's own 429
rather than a silent sleep.
"""
from aaa.platform.rate_limit.limiter import (  # noqa: F401
    MAX_REQUESTS_PER_WINDOW,
    WINDOW_SECONDS,
    FixedWindowLimiter,
)

_NVIDIA_PREFIX = "nvidia_nim/"
_OPENROUTER_PREFIX = "openrouter/"

#: OpenRouter's published per-minute cap for ``:free`` routes.
OPENROUTER_REQUESTS_PER_WINDOW: int = 20

_nvidia_limiter = FixedWindowLimiter()
_openrouter_limiter = FixedWindowLimiter(
    max_requests=OPENROUTER_REQUESTS_PER_WINDOW, window_seconds=WINDOW_SECONDS)


async def acquire_for_model(model: str) -> None:
    """Wait for rate-limit clearance when *model* targets a throttled provider.

    :param model: LiteLLM model string (e.g. ``"openrouter/nvidia/..."``).
    :type model: str
    :returns: None
    """
    if model.startswith(_NVIDIA_PREFIX):
        await _nvidia_limiter.acquire()
    elif model.startswith(_OPENROUTER_PREFIX):
        await _openrouter_limiter.acquire()


__all__ = [
    'FixedWindowLimiter',
    'MAX_REQUESTS_PER_WINDOW',
    'OPENROUTER_REQUESTS_PER_WINDOW',
    'WINDOW_SECONDS',
    'acquire_for_model',
]
