"""Part 2 of the former ``flex_retry`` module (auto-split)."""
from __future__ import annotations

from typing import Any

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
from aaa.platform.flex_retry.one_call import _acompletion_once


async def flex_acompletion(**kwargs: Any) -> Any:
    """Async LiteLLM call with transient retry, Flex retry + standard-tier fallback.

    This is the one place the provider is called, so it is where fix 39's
    retry belongs: every caller — the phase agents, the Verifier, the
    Orchestrator's decide loop, the tier-3 spawns — inherits it by inheriting
    this function. See :mod:`aaa.platform.transient_retry` for what counts as
    transient and for the budget rule that decides whether the retry is
    affordable.

    Parameters
    ----------
    **kwargs:
        Any keyword arguments accepted by ``litellm.acompletion``.  When
        ``service_tier="flex"`` is present the extended timeout and backoff
        logic are activated; otherwise this is a thin pass-through with the
        default timeout applied.
    """
    from aaa.platform.transient_retry import with_transient_retry
    return await with_transient_retry(_acompletion_once, **kwargs)
