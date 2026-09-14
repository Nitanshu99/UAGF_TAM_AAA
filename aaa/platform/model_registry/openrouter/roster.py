"""openrouter_roster.py — OpenRouter mirror of ``AGENT_MODELS``.

Selected via ``PROVIDER=openrouter``. OpenRouter is an aggregator: the slug
below is a *route*, and the upstream provider actually serving it can vary,
which is why the Stage B provenance contract asks customers on OpenRouter to
record `upstream_provider` alongside the slug.

The ``:free`` variant is used deliberately. Its published limits are 20
requests per minute, and 50 requests per day on an account that has never
purchased credits (1000/day once $10 has been bought at any point) — see
:mod:`aaa.platform.rate_limit`, which throttles the per-minute cap. The daily
cap is *not* something a limiter can wait out: a single mock case uses ~56 LLM
calls, so an *unfunded* account cannot complete one engagement here.

**This is the default route since 2026-09-09**, and the paragraph above is why
the distinction matters rather than an argument against it: the repo's account
reports ``is_free_tier: false``, so it carries the 1000/day cap, not the 50/day
one, and a full engagement fits comfortably.

The switch was forced by measurement, not preference. NVIDIA NIM exhausted its
free-tier quota mid-run that day — 34 of 54 calls failed, degrading into ``429``
then ``503`` then ``404``, and the engagement produced a report whose every
narrative section had fallen back to deterministic assembly. On the same roster
model the OpenRouter route answered a probe in **14 s** against NIM's 100–500 s
per call. ``PROVIDER=nvidia`` remains supported and is the fallback if this
route degrades in turn.
"""
from __future__ import annotations

import logging
import os

from aaa.platform.model_registry.model_config import ModelConfig

logger = logging.getLogger(__name__)

#: Context window advertised for the ``:free`` route (the paid variant of the
#: same model publishes 512288). Declared so the token guard sizes budgets
#: against what this route actually serves.
_CONTEXT_WINDOW = 1_000_000

def _ultra() -> ModelConfig:
    """The roster's one model, on the free route unless an endpoint is pinned.

    ``OPENROUTER_PROVIDER`` selects a specific serving endpoint, which only the
    paid slug exposes — the ``:free`` route is a single gated endpoint with
    nothing to choose between. Pinning therefore switches the slug and takes
    that endpoint's own published context window; see
    :mod:`aaa.platform.model_registry.openrouter.provider`.
    """
    from aaa.platform.model_registry.openrouter.provider import (
        DEFAULT_MODEL,
        pinned_context_window,
        pinned_model,
    )
    window = pinned_context_window()
    if window is None:
        # M19: `OPENROUTER_MODEL` is read only on the pinned branch below, so
        # setting it alone selects nothing and used to say nothing either —
        # `pinned_model()` is not called here, so even its unrecognised-slug
        # error never fired. A run asked for minimax/minimax-m3, was served
        # nvidia/nemotron-3-ultra on the free route, and the log recorded no
        # trace of the substitution. Discarded, but never quietly.
        asked = os.environ.get("OPENROUTER_MODEL", "").strip()
        if asked and asked.lower() != DEFAULT_MODEL:
            logger.warning(
                "OPENROUTER_MODEL=%r selects nothing on its own: the free route "
                "serves %s:free. Set OPENROUTER_PROVIDER to one of that model's "
                "endpoints to switch to the paid slug, which is the only way to "
                "choose a model here.", asked, DEFAULT_MODEL)
        return ModelConfig(f"openrouter/{DEFAULT_MODEL}:free",
                           context_window=_CONTEXT_WINDOW)
    return ModelConfig(f"openrouter/{pinned_model()}", context_window=window)


_ULTRA = _ultra()

OPENROUTER_AGENT_MODELS: dict[str, ModelConfig] = {
    "Orchestrator":         _ULTRA,
    "Verifier":             _ULTRA,
    "Regulatory RAG":       _ULTRA,
    "ScopeAgent":           _ULTRA,
    "DataAuditor":          _ULTRA,
    "ModelValidator":       _ULTRA,
    "OutputFairnessTester": _ULTRA,
    "GovernanceAgent":      _ULTRA,
    "ReportArchitect":      _ULTRA,
    "UAGF-TAM-L":           _ULTRA,
    "CyberSecurityAgent":   _ULTRA,
    "PrivacyDPOAgent":      _ULTRA,
    "DocIntelligenceAgent": _ULTRA,
    "ClientBrief":          _ULTRA,
}
