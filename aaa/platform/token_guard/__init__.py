"""token_guard — pre-flight token budgeting for every LLM call (§8.1).

Wraps ``litellm.token_counter`` and ``litellm.get_model_info`` so callers can
assert that an outgoing prompt fits inside the model's input window before
the request leaves the process.  Budget = ``max_input_tokens * threshold``
minus a reserve for the response.

The 0.8 default leaves 20 % headroom for tokenizer drift between models and
for the chat-completion wrapper bytes that LiteLLM adds to every request.

Falls back to a length-based heuristic (1 token ≈ 4 chars) when LiteLLM is
not installed or the model is not in its cost map."""
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
    'logger',
    'DEFAULT_THRESHOLD',
    'DEFAULT_RESERVE_OUTPUT',
    '_FALLBACK_CONTEXT_WINDOW',
    '_FALLBACK_CHARS_PER_TOKEN',
    'BudgetExceededError',
    'count_tokens',
    'get_context_window',
    'compute_budget',
    'ensure_within_budget',
]
