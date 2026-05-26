"""
Unit tests for aaa.platform.token_guard.

Covers:
  - count_tokens with LiteLLM available (small text → small count)
  - count_tokens falls back to char/4 heuristic when LiteLLM raises
  - get_context_window returns ≥ 100k for known Claude/GPT models
  - get_context_window falls back to 200k when model is unknown
  - compute_budget = window * threshold - reserve_for_output
  - ensure_within_budget returns count on pass
  - ensure_within_budget raises BudgetExceededError on fail
"""
from __future__ import annotations

import pytest

from aaa.platform import token_guard
from aaa.platform.token_guard import (
    BudgetExceededError,
    DEFAULT_RESERVE_OUTPUT,
    DEFAULT_THRESHOLD,
    compute_budget,
    count_tokens,
    ensure_within_budget,
    get_context_window,
)


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------

def test_count_tokens_returns_positive_int_for_text():
    n = count_tokens("claude-opus-4-5", text="hello world")
    assert isinstance(n, int)
    assert n >= 1


def test_count_tokens_scales_with_length():
    short = count_tokens("claude-opus-4-5", text="hi")
    long = count_tokens("claude-opus-4-5", text="hi " * 500)
    assert long > short


def test_count_tokens_messages_form():
    n = count_tokens(
        "claude-opus-4-5",
        messages=[{"role": "user", "content": "hello world"}],
    )
    assert n >= 1


def test_count_tokens_falls_back_when_litellm_unavailable(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def _fail(name, *a, **kw):
        if name == "litellm":
            raise ImportError("simulated missing litellm")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _fail)
    n = count_tokens("claude-opus-4-5", text="x" * 400)
    # Fallback heuristic: 400 chars / 4 = 100 tokens
    assert n == 100


# ---------------------------------------------------------------------------
# get_context_window + compute_budget
# ---------------------------------------------------------------------------

def test_get_context_window_known_model():
    w = get_context_window("claude-opus-4-5")
    assert w >= 100_000


def test_get_context_window_unknown_model_uses_fallback():
    w = get_context_window("not-a-real-model-xyz-9999")
    assert w == token_guard._FALLBACK_CONTEXT_WINDOW


def test_compute_budget_formula():
    window = get_context_window("claude-opus-4-5")
    budget = compute_budget("claude-opus-4-5")
    expected = int(window * DEFAULT_THRESHOLD) - DEFAULT_RESERVE_OUTPUT
    assert budget == expected


def test_compute_budget_custom_threshold():
    budget_low = compute_budget("claude-opus-4-5", threshold=0.5)
    budget_high = compute_budget("claude-opus-4-5", threshold=0.9)
    assert budget_low < budget_high


def test_compute_budget_is_never_below_one():
    budget = compute_budget(
        "claude-opus-4-5", threshold=0.0001, reserve_for_output=10_000_000
    )
    assert budget == 1


# ---------------------------------------------------------------------------
# ensure_within_budget
# ---------------------------------------------------------------------------

def test_ensure_within_budget_pass_returns_token_count():
    n = ensure_within_budget("a short prompt", "claude-opus-4-5")
    assert isinstance(n, int)
    assert n >= 1


def test_ensure_within_budget_raises_when_over():
    # threshold=0.000001 → budget = max(1, int(200_000 * 0.000001) − 0) = 1
    # Any non-trivial text will have > 1 token and must raise.
    with pytest.raises(BudgetExceededError) as exc:
        ensure_within_budget(
            "x " * 50,
            "claude-opus-4-5",
            threshold=0.000001,
            reserve_for_output=0,
        )
    assert exc.value.model == "claude-opus-4-5"
    assert exc.value.prompt_tokens > exc.value.budget


def test_budget_exceeded_error_includes_diagnostics():
    err = BudgetExceededError(prompt_tokens=999, budget=100, model="m")
    assert err.prompt_tokens == 999
    assert err.budget == 100
    assert err.model == "m"
    assert "999" in str(err) and "100" in str(err) and "'m'" in str(err)
