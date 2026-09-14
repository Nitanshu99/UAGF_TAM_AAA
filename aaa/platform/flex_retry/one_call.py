"""A single LiteLLM call: the client ceiling, the Flex fallback and the transient retry."""
from __future__ import annotations

from typing import Any

from aaa.platform.flex_retry.ladder import flex_ladder
from aaa.platform.flex_retry.logger import (
    CLIENT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    FLEX_TIMEOUT_SECONDS,
)


async def _acompletion_once(**kwargs: Any) -> Any:
    """One pass of the Flex ladder: rate-limit backoff, then standard-tier fallback.

    Everything a *single* transient-retry attempt covers. The Flex ladder's own
    429 retries stay inside here deliberately: rate limiting and momentary
    unavailability are different failures with different remedies, and nesting
    them keeps each bounded by its own ceiling rather than by their product.
    """
    import litellm  # type: ignore  # optional at import time

    from aaa.platform.transient_retry.budget import ATTEMPT_CEILING
    ceiling = kwargs.pop(ATTEMPT_CEILING, None)  # set when the fallback's time is reserved (T-085)

    from aaa.observability.tracing import configure_llm_tracing
    configure_llm_tracing()

    from aaa.platform.rate_limit import acquire_for_model
    await acquire_for_model(kwargs.get("model", ""))

    # Greedy by default, so the same evidence yields the same critique and a run
    # can be reproduced (T-20260913-001). Applied here, before `call_kwargs` and
    # the ladder's fallback are built, so every attempt inherits it. The caller's
    # own value wins, which leaves an escape hatch for deliberate sampling.
    #
    # The request is model-aware: OpenAI's reasoning models take no temperature
    # (`decoding.capability`). `drop_params` is the safety net for anything else a
    # provider refuses, set per call rather than on litellm's global flag so
    # nothing else in the process changes. It drops silently, which is why the
    # audit row records what was sent as well as what was asked for.
    from aaa.platform.model_registry.decoding import decoding_kwargs
    kwargs = {"drop_params": True, **decoding_kwargs(kwargs.get("model", "")), **kwargs}

    is_flex = kwargs.get("service_tier") == "flex"
    # Fix 37 (R6): inside a phase, the client ceiling *is* the phase's remaining
    # budget — one number, two consumers, so they cannot drift apart again.
    # Outside one, an explicit ceiling from the caller wins: agents differ in how
    # long their work legitimately takes, and one global constant abandoned the
    # Verifier's slowest calls while the same provider was completing them
    # (P6, P8). See `model_registry.timeouts.resolve_client_timeout`.
    from aaa.platform.model_registry.timeouts import resolve_client_timeout
    default = FLEX_TIMEOUT_SECONDS if is_flex else DEFAULT_TIMEOUT_SECONDS
    timeout = resolve_client_timeout(kwargs.get("timeout"), default)
    timeout = timeout if ceiling is None else min(timeout, ceiling)
    # Fix 46 (R14): `timeout` is a **per-attempt** ceiling in the client beneath
    # litellm, and `max_retries` defaults to 2 there — so a ceiling of N seconds
    # bounded 3N seconds of wall-clock while the audit trail recorded the whole
    # sequence. Setting it to 0 makes the ceiling bound what its name says and
    # leaves this codebase's own retry (fix 39) as the only one, measured and on
    # the record. See `model_registry.timeouts` for the evidence.
    from aaa.platform.model_registry.openrouter.provider import provider_routing
    call_kwargs = {**kwargs, "timeout": timeout,
                   "max_retries": kwargs.get("max_retries", CLIENT_MAX_RETRIES),
                   **provider_routing(kwargs.get("model", ""))}

    if not is_flex:
        # Non-Flex: single attempt, no special handling.
        return await litellm.acompletion(**call_kwargs)

    return await flex_ladder(litellm, call_kwargs, kwargs, timeout)


__all__ = ["_acompletion_once"]
