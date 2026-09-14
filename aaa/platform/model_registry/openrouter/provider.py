"""Pin OpenRouter to one serving endpoint, when asked — ``OPENROUTER_PROVIDER``.

OpenRouter fronts a pool of providers for the same model id and picks one per
call. That is usually what you want; it is not what you want when the pool's
members differ in ways the run depends on. For
``nvidia/nemotron-3-ultra-550b-a55b`` the catalogue lists three, and they differ
in **context window** (202,800 to 262,144), in quantisation (fp4 or fp8) and in
price — so an unpinned run can silently size a token budget against 262,144 and
then be served by an endpoint offering 202,800.

Unset, nothing here applies and the default free route is used as before. Set,
two things follow together, because they are one decision:

* the **paid** model slug is selected — provider pinning has no meaning on the
  ``:free`` route, which is a single gated endpoint; and
* the pinned endpoint's own published context window replaces the roster's, so
  :func:`aaa.platform.token_guard.get_context_window` sizes against what this
  endpoint actually serves.

Windows below are read from OpenRouter's ``/models/…/endpoints`` catalogue on
2026-09-10, not estimated. An unrecognised value is refused rather than guessed:
the roster's own docstring is right that a guessed window is worse than a
logged unknown, and it is worse here in particular, because the guard would be
permitting headroom the endpoint does not have.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from aaa.platform.model_registry.openrouter.catalogue import DEFAULT_MODEL, PINNABLE_ENDPOINTS

logger = logging.getLogger(__name__)

def pinned_model() -> str:
    """The model slug ``OPENROUTER_MODEL`` names, or :data:`DEFAULT_MODEL`.

    An unrecognised slug is refused for the same reason an unrecognised endpoint
    is: this module's only claim to authority is that its context windows were
    read from the catalogue, and it has none for a model nobody has looked up.
    """
    raw = os.environ.get("OPENROUTER_MODEL", "").strip().lower()
    if not raw:
        return DEFAULT_MODEL
    if raw not in PINNABLE_ENDPOINTS:
        logger.error(
            "OPENROUTER_MODEL=%r is not a model this repo has published context "
            "windows for (%s). Falling back to %s.",
            raw, ", ".join(sorted(PINNABLE_ENDPOINTS)), DEFAULT_MODEL)
        return DEFAULT_MODEL
    return raw


def pinned_endpoint() -> str | None:
    """The endpoint slug ``OPENROUTER_PROVIDER`` names, or ``None``.

    ``none`` is an explicit choice of the free route: the bootstrap fills a blank value
    with the reference configuration, so a blank cannot express it (T-20260914-066).

    :returns: An endpoint of the selected model, or ``None`` when unset, ``none``, or not
        one this repo has a window for (which is logged, not silently ignored).
    """
    raw = os.environ.get("OPENROUTER_PROVIDER", "").strip().lower()
    if not raw or raw == "none":
        return None
    known = PINNABLE_ENDPOINTS[pinned_model()]
    if raw not in known:
        logger.error(
            "OPENROUTER_PROVIDER=%r is not an endpoint of %s that this repo has a "
            "published context window for (%s). Ignoring the pin rather than "
            "sizing token budgets against a guess.",
            raw, pinned_model(), ", ".join(sorted(known)))
        return None
    return raw


def pinned_context_window() -> int | None:
    """The published window of the pinned endpoint, or ``None`` when unpinned."""
    endpoint = pinned_endpoint()
    return PINNABLE_ENDPOINTS[pinned_model()][endpoint] if endpoint else None


def provider_routing(model: str) -> dict[str, Any]:
    """Return the ``extra_body`` that pins *model* to the configured endpoint.

    ``allow_fallbacks: false`` is deliberate. A pin that silently falls back to
    another endpoint is not a pin: the run would be served by a provider whose
    context window the token guard was not sized against, which is the failure
    the pin exists to prevent.

    :param model: The LiteLLM model string about to be called.
    :returns: ``{"extra_body": {...}}`` when a pin applies, else ``{}``.
    """
    endpoint = pinned_endpoint()
    if not endpoint or not model.startswith("openrouter/"):
        return {}
    return {"extra_body": {"provider": {"only": [endpoint], "allow_fallbacks": False}}}


__all__ = ["DEFAULT_MODEL", "PINNABLE_ENDPOINTS", "pinned_model", "pinned_endpoint",
           "pinned_context_window", "provider_routing"]
