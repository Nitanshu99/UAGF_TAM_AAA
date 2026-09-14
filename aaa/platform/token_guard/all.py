"""Part 3 of the former ``token_guard`` module (auto-split)."""
from __future__ import annotations

from aaa.platform.token_guard.get_context_window import (  # noqa: F401
    compute_budget,
    ensure_within_budget,
    get_context_window,
)
from aaa.platform.token_guard.logger import (  # noqa: F401
    _FALLBACK_CHARS_PER_TOKEN,
    _FALLBACK_CONTEXT_WINDOW,
    DEFAULT_RESERVE_OUTPUT,
    DEFAULT_THRESHOLD,
    BudgetExceededError,
    count_tokens,
    logger,
)

__all__ = [
    "BudgetExceededError",
    "DEFAULT_THRESHOLD",
    "DEFAULT_RESERVE_OUTPUT",
    "compute_budget",
    "count_tokens",
    "ensure_within_budget",
    "get_context_window",
]
