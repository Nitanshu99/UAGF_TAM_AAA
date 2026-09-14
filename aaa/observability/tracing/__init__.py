"""LiteLLM → Langfuse tracing wiring — the single seam for every LLM call.

Called from :func:`aaa.platform.flex_retry.flex_acompletion` before the first
completion. No-op when Langfuse credentials are not configured, so tests and
CI (which never set them) are unaffected.
"""
from __future__ import annotations

import logging
import os

from aaa.observability.tracing.flush import drain_llm_callbacks, flush_llm_tracing
from aaa.observability.tracing.state import is_llm_tracing_configured, set_llm_tracing_configured

logger = logging.getLogger(__name__)


#: LiteLLM callback name. ``langfuse_otel`` targets the OTEL-based Langfuse
#: SDK (v3+); the legacy ``langfuse`` callback reads ``langfuse.version``,
#: which the installed v4 SDK no longer exposes (it raises on every call).
_CALLBACK = "langfuse_otel"


#: Placeholder values shipped by earlier ``.env.example`` revisions. Blanking
#: the template only helps new checkouts — an existing ``.env`` still carries
#: ``LANGFUSE_SECRET_KEY=changeme``, which is non-empty and so used to switch
#: tracing on with credentials that were never valid project keys. Every call
#: then failed at the exporter instead of at configuration time.
_PLACEHOLDER_KEYS = frozenset({"changeme", "change-me", "changeme-salt", "...", "your-key-here"})


def _is_real_key(value: str | None) -> bool:
    """Return whether *value* is a usable credential rather than a placeholder.

    :param value: Configured key, possibly blank or a template placeholder.
    :type value: str | None
    :returns: ``True`` when the value looks like a real credential.
    :rtype: bool
    """
    return bool(value) and value.strip().lower() not in _PLACEHOLDER_KEYS


def configure_llm_tracing() -> bool:
    """Register Langfuse as a LiteLLM success/failure callback, once.

    :returns: ``True`` when tracing is active (now or from a prior call);
        ``False`` when Langfuse credentials are not configured.
    :rtype: bool
    """
    if is_llm_tracing_configured():
        return True
    from aaa.settings import settings
    public, secret = settings.langfuse_public_key, settings.langfuse_secret_key
    if not (_is_real_key(public) and _is_real_key(secret)):
        if public or secret:
            logger.warning(
                "Langfuse tracing disabled: LANGFUSE_PUBLIC_KEY/SECRET_KEY still hold "
                "template placeholders. Paste a real project's keys from %s.",
                settings.langfuse_host,
            )
        return False

    import litellm  # type: ignore

    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)
    if _CALLBACK not in litellm.success_callback:
        litellm.success_callback.append(_CALLBACK)
    if _CALLBACK not in litellm.failure_callback:
        litellm.failure_callback.append(_CALLBACK)

    set_llm_tracing_configured(True)
    logger.info("Langfuse LLM tracing enabled (host=%s)", settings.langfuse_host)
    return True



def reset_llm_tracing_state() -> None:
    """Reset the idempotency latch — test-only helper."""
    set_llm_tracing_configured(False)


__all__ = [
    "configure_llm_tracing",
    "drain_llm_callbacks", "flush_llm_tracing",
    "is_llm_tracing_configured",
    "reset_llm_tracing_state",
]
