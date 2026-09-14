"""Part 1 of the former ``token_guard`` module (auto-split)."""
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
    signal in minimal-install environments.
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
