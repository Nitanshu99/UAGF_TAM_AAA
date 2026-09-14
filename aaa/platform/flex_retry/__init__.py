"""flex_retry — Exponential-backoff wrapper for LiteLLM calls with Flex Processing.

OpenAI Flex Processing (``service_tier="flex"``) uses spare capacity, so callers
may receive a ``429 Resource Unavailable`` during peak load.  This module wraps
``litellm.acompletion`` with:

1. **Extended timeout** — 240 s for Flex calls; 120 s otherwise. Both are
   overridable (``FLEX_TIMEOUT_SECONDS`` / ``LLM_TIMEOUT_SECONDS``) because
   rate-limited providers queue rather than reject: the NVIDIA NIM free tier
   can hold a request past the ceiling, which surfaces as ``litellm.Timeout``
   and truncates the audit mid-run.
2. **Exponential backoff** — up to ``FLEX_MAX_RETRIES`` on any ``429``/
   ``RateLimitError`` before giving up on Flex.
3. **Automatic fallback** — after exhausting Flex retries, the call is retried
   once on the *standard* tier (``service_tier`` removed) so the audit is never
   completely stalled by spare-capacity exhaustion.

Usage (lowest-level, used internally by ``BaseAgent.acompletion``)::

    from aaa.platform.flex_retry import flex_acompletion

    response = await flex_acompletion(
        model="gpt-5.6-luna",
        service_tier="flex",
        messages=[{"role": "user", "content": "…"}],
    )

Post-GPT-5.6 migration no registry entry ships a Flex tier (only
``gpt-5.6-luna`` supports it); this module stays for explicit Luna
overrides via ``resolve_service_tier``'s override parameter."""
from aaa.platform.flex_retry.flex_acompletion import flex_acompletion  # noqa: F401
from aaa.platform.flex_retry.logger import (  # noqa: F401
    CLIENT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    FLEX_BACKOFF_BASE,
    FLEX_MAX_RETRIES,
    FLEX_TIMEOUT_SECONDS,
    _is_rate_limit,
    _strip_flex,
    logger,
)

__all__ = [
    'logger',
    'CLIENT_MAX_RETRIES',
    'FLEX_TIMEOUT_SECONDS',
    'DEFAULT_TIMEOUT_SECONDS',
    'FLEX_MAX_RETRIES',
    'FLEX_BACKOFF_BASE',
    '_is_rate_limit',
    '_strip_flex',
    'flex_acompletion',
]
