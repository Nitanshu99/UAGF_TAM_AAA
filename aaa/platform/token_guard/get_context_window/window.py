"""Resolve a model's usable input-context window.

Three sources in priority order: the agent roster's declared
``ModelConfig.context_window``, LiteLLM's cost map, then a generic fallback.
The fallback is deliberately noisy — a budget derived from it is not
model-specific, which silently disarms the guard for that model.
"""
from __future__ import annotations

from aaa.platform.token_guard.logger import _FALLBACK_CONTEXT_WINDOW, logger


def _declared_window(model: str) -> int | None:
    """Return the roster-declared context window for *model*, if any.

    Searches *every* roster, not just the active one: a model id belongs to
    exactly one provider, and consulting only ``AGENT_MODELS`` meant a window
    declared on a NIM config was never found — leaving precisely the
    ``nvidia_nim/*`` ids this field exists for on the generic fallback.

    The OpenRouter roster was added after that fix and not added here, so the
    same defect ran again on the provider that has since become the default.
    It is worse there, because OpenRouter fronts many endpoints per model and
    LiteLLM's map answers for the *model*: pinned to CoreWeave, which serves
    262,144 tokens, the guard was sizing budgets against the 1,048,576 the map
    reports for ``minimax/minimax-m3`` — permitting four times what the endpoint
    accepts, and permissively, which is the direction that does not fail loudly.

    :param model: Fully-qualified LiteLLM model id.
    :type model: str
    :returns: Declared ``context_window``, or ``None`` when undeclared.
    :rtype: int | None
    """
    try:
        from aaa.platform.model_registry.nvidia_roster import NVIDIA_AGENT_MODELS
        from aaa.platform.model_registry.openrouter.roster import OPENROUTER_AGENT_MODELS
        from aaa.platform.model_registry.roster import AGENT_MODELS

        for roster in (AGENT_MODELS, NVIDIA_AGENT_MODELS, OPENROUTER_AGENT_MODELS):
            for config in roster.values():
                if config.model == model and config.context_window:
                    return int(config.context_window)
    except Exception as exc:  # noqa: BLE001
        logger.debug("model registry unavailable for %s (%s).", model, exc)
    return None


def get_context_window(model: str) -> int:
    """Return ``max_input_tokens`` for *model*.

    Resolution order: the roster's declared ``context_window``, then LiteLLM's
    cost map, then a generic fallback. The fallback is logged at warning level
    because a budget computed from it does not reflect the model — the guard
    stops guarding for that model rather than failing loudly, which is how it
    went unnoticed for every ``nvidia_nim/*`` id (none are in the cost map).

    :param model: Fully-qualified LiteLLM model id.
    :type model: str
    :returns: Usable input-token window for *model*.
    :rtype: int
    """
    declared = _declared_window(model)
    if declared:
        return declared
    try:
        import litellm  # type: ignore

        info = litellm.get_model_info(model)
        window = info.get("max_input_tokens") or info.get("max_tokens")
        if window:
            return int(window)
    except Exception as exc:  # noqa: BLE001
        logger.debug("litellm.get_model_info unavailable for %s (%s).", model, exc)
    logger.warning(
        "No context window known for %s — using the generic %d-token fallback, so the "
        "token budget is not model-specific. Declare ModelConfig.context_window to fix.",
        model, _FALLBACK_CONTEXT_WINDOW,
    )
    return _FALLBACK_CONTEXT_WINDOW
