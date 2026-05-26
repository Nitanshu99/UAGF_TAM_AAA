"""
token_guard — pre-flight token budgeting for every LLM call (§8.1).

Wraps ``litellm.token_counter`` and ``litellm.get_model_info`` so callers can
assert that an outgoing prompt fits inside the model's input window before
the request leaves the process.  Budget = ``max_input_tokens * threshold``
minus a reserve for the response.

The 0.8 default leaves 20 % headroom for tokenizer drift between models and
for the chat-completion wrapper bytes that LiteLLM adds to every request.

Falls back to a length-based heuristic (1 token ≈ 4 chars) when LiteLLM is
not installed or the model is not in its cost map.
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD: float = 0.8
DEFAULT_RESERVE_OUTPUT: int = 8_192
_FALLBACK_CONTEXT_WINDOW: int = 200_000
_FALLBACK_CHARS_PER_TOKEN: int = 4


class BudgetExceededError(Exception):
    """Raised when an outgoing prompt would exceed the allowed token budget."""

    def __init__(self, prompt_tokens: int, budget: int, model: str):
        self.prompt_tokens = prompt_tokens
        self.budget = budget
        self.model = model
        super().__init__(
            f"Prompt of {prompt_tokens} tokens exceeds budget {budget} "
            f"for model '{model}'."
        )


def count_tokens(
    model: str,
    text: str | None = None,
    messages: Sequence[dict[str, Any]] | None = None,
) -> int:
    """Return the token count for *text* or *messages* under *model*.

    Uses ``litellm.token_counter`` when available; otherwise falls back to
    a 1-token-per-4-characters heuristic so the guard still gives a useful
    signal in offline / minimal-install environments.
    """
    try:
        import litellm  # type: ignore

        if messages is not None:
            return int(litellm.token_counter(model=model, messages=list(messages)))
        return int(litellm.token_counter(model=model, text=text or ""))
    except Exception as exc:  # noqa: BLE001
        logger.debug("litellm.token_counter unavailable (%s); using fallback.", exc)
        if messages is not None:
            chars = sum(len(str(m.get("content", ""))) for m in messages)
        else:
            chars = len(text or "")
        return max(1, chars // _FALLBACK_CHARS_PER_TOKEN)


def get_context_window(model: str) -> int:
    """Return ``max_input_tokens`` for *model* (LiteLLM cost map)."""
    try:
        import litellm  # type: ignore

        info = litellm.get_model_info(model)
        window = info.get("max_input_tokens") or info.get("max_tokens")
        if window:
            return int(window)
    except Exception as exc:  # noqa: BLE001
        logger.debug("litellm.get_model_info unavailable for %s (%s).", model, exc)
    return _FALLBACK_CONTEXT_WINDOW


def compute_budget(
    model: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    reserve_for_output: int = DEFAULT_RESERVE_OUTPUT,
) -> int:
    """Return the maximum input-token count allowed for *model*."""
    window = get_context_window(model)
    budget = int(window * threshold) - reserve_for_output
    return max(1, budget)


def ensure_within_budget(
    text: str,
    model: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    reserve_for_output: int = DEFAULT_RESERVE_OUTPUT,
) -> int:
    """Assert that *text* fits inside the budget for *model*.

    Returns the measured token count on success; raises
    :class:`BudgetExceededError` otherwise.  Call **immediately before**
    handing the prompt to ``litellm.acompletion`` so over-large requests
    are caught locally instead of failing on the provider side.
    """
    budget = compute_budget(
        model, threshold=threshold, reserve_for_output=reserve_for_output
    )
    n = count_tokens(model, text=text)
    if n > budget:
        raise BudgetExceededError(prompt_tokens=n, budget=budget, model=model)
    return n


__all__ = [
    "BudgetExceededError",
    "DEFAULT_THRESHOLD",
    "DEFAULT_RESERVE_OUTPUT",
    "compute_budget",
    "count_tokens",
    "ensure_within_budget",
    "get_context_window",
]
