"""token_guard: ensure_within_budget pass / fail behaviour."""
from __future__ import annotations

import pytest

from aaa.platform.token_guard import BudgetExceededError, ensure_within_budget


def test_ensure_within_budget_pass_returns_token_count():
    n = ensure_within_budget("claude-opus-4-5", "a short prompt")
    assert isinstance(n, int)
    assert n >= 1


def test_ensure_within_budget_pass_with_messages():
    n = ensure_within_budget(
        "claude-opus-4-5", messages=[{"role": "user", "content": "hello world"}])
    assert isinstance(n, int)
    assert n >= 1


def test_ensure_within_budget_raises_when_over():
    # threshold=0.000001 → budget = max(1, int(200_000 * 0.000001) − 0) = 1
    # Any non-trivial text will have > 1 token and must raise.
    with pytest.raises(BudgetExceededError) as exc:
        ensure_within_budget("claude-opus-4-5", "x " * 50,
                             threshold=0.000001, reserve_for_output=0)
    assert exc.value.model == "claude-opus-4-5"
    assert exc.value.prompt_tokens > exc.value.budget


def test_ensure_within_budget_raises_when_over_messages():
    """messages= form also enforces the budget."""
    with pytest.raises(BudgetExceededError) as exc:
        ensure_within_budget(
            "claude-opus-4-5",
            messages=[{"role": "user", "content": "x " * 50}],
            threshold=0.000001, reserve_for_output=0)
    assert exc.value.model == "claude-opus-4-5"
    assert exc.value.prompt_tokens > exc.value.budget


def test_budget_exceeded_error_includes_diagnostics():
    err = BudgetExceededError(prompt_tokens=999, budget=100, model="m")
    assert err.prompt_tokens == 999
    assert err.budget == 100
    assert err.model == "m"
    assert "999" in str(err) and "100" in str(err) and "'m'" in str(err)
