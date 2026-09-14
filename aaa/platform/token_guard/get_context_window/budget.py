"""Token budget derivation and enforcement for a resolved context window.

Separated from :mod:`window` so window *resolution* (registry, cost map,
fallback) stays independent of the *policy* applied to it.
"""
from __future__ import annotations

from typing import Any, Sequence

from aaa.platform.token_guard.get_context_window.window import get_context_window
from aaa.platform.token_guard.logger import (
    DEFAULT_RESERVE_OUTPUT,
    DEFAULT_THRESHOLD,
    BudgetExceededError,
    count_tokens,
)


def compute_budget(
    model: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    reserve_for_output: int = DEFAULT_RESERVE_OUTPUT,
) -> int:
    """Return the maximum input-token count allowed for *model*.

    :param model: Fully-qualified LiteLLM model id.
    :type model: str
    :param threshold: Fraction of the window usable by the prompt.
    :type threshold: float
    :param reserve_for_output: Tokens held back for the response.
    :type reserve_for_output: int
    :returns: Allowed input-token count, never below 1.
    :rtype: int
    """
    window = get_context_window(model)
    budget = int(window * threshold) - reserve_for_output
    return max(1, budget)


def ensure_within_budget(
    model: str,
    text: str | None = None,
    *,
    messages: Sequence[dict[str, Any]] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    reserve_for_output: int = DEFAULT_RESERVE_OUTPUT,
) -> int:
    """Assert that *text* or *messages* fits inside the budget for *model*.

    Pass either ``text`` (plain string) or ``messages`` (chat payload list);
    the token count is computed with :func:`count_tokens` in both cases.

    Call **immediately before** handing the prompt to ``litellm.acompletion``
    so over-large requests are caught locally instead of failing on the
    provider side.

    :param model: Fully-qualified LiteLLM model id.
    :type model: str
    :param text: Plain-string prompt, mutually exclusive with *messages*.
    :type text: str | None
    :param messages: Chat payload, mutually exclusive with *text*.
    :type messages: Sequence[dict[str, Any]] | None
    :param threshold: Fraction of the window usable by the prompt.
    :type threshold: float
    :param reserve_for_output: Tokens held back for the response.
    :type reserve_for_output: int
    :returns: The measured token count.
    :rtype: int
    :raises BudgetExceededError: If the prompt exceeds the computed budget.
    """
    budget = compute_budget(
        model, threshold=threshold, reserve_for_output=reserve_for_output
    )
    n = count_tokens(model, text=text, messages=messages)
    if n > budget:
        raise BudgetExceededError(prompt_tokens=n, budget=budget, model=model)
    return n
