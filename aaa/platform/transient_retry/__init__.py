"""transient_retry — bounded, backed-off retries past a momentary provider failure.

Fix 39, findings **R7** and **R13**. Before it there was no retry anywhere in
the provider path: seven calls in the 2026-09-03 five-case run failed, and the
cost each time was not the call but a whole phase — or, once, the Orchestrator's
own turn, which ended LLM-driven sequencing for the rest of that engagement.

The retry sits at the lowest level, inside
:func:`aaa.platform.flex_retry.flex_acompletion`, so every caller inherits it:
the phase agents, the Verifier, the Orchestrator's decide loop and the tier-3
spawns. It is bounded in three ways at once — a few retries
(:data:`~aaa.platform.transient_retry.retry.MAX_TRANSIENT_RETRIES`) with capped
exponential backoff and jitter, and only for failures :func:`~.classify.is_transient`
positively recognises — and it never runs when the phase has no budget left for it.

Three modules, three concerns:

* :mod:`.classify` — what counts as transient, and why a timeout and a 429 do not
* :mod:`.retry` — the bounded loop and the budget rule
* :mod:`.attempts` — how a recovered call is distinguished in the audit trail
"""
from aaa.platform.transient_retry.attempts import (  # noqa: F401
    note_fallback,
    note_retry,
    record_attempts,
    served_model_so_far,
)
from aaa.platform.transient_retry.classify import is_transient  # noqa: F401
from aaa.platform.transient_retry.fallback import FALLBACK_MODELS, fallback_model_for  # noqa: F401
from aaa.platform.transient_retry.retry import (  # noqa: F401
    MAX_TRANSIENT_RETRIES,
    TRANSIENT_BACKOFF_CAP_SECONDS,
    TRANSIENT_BACKOFF_SECONDS,
    backoff_seconds,
    with_transient_retry,
)

__all__ = [
    "FALLBACK_MODELS",
    "fallback_model_for",
    "note_fallback",
    "served_model_so_far",
    "is_transient",
    "with_transient_retry",
    "record_attempts",
    "note_retry",
    "MAX_TRANSIENT_RETRIES",
    "TRANSIENT_BACKOFF_SECONDS",
    "TRANSIENT_BACKOFF_CAP_SECONDS",
    "backoff_seconds",
]
