"""token_guard: count_tokens, context-window lookup and budget formula."""
from __future__ import annotations

from aaa.platform import token_guard
from aaa.platform.token_guard import (
    DEFAULT_RESERVE_OUTPUT,
    DEFAULT_THRESHOLD,
    compute_budget,
    count_tokens,
    get_context_window,
)


def test_count_tokens_returns_positive_int_for_text():
    n = count_tokens("claude-opus-4-5", text="hello world")
    assert isinstance(n, int)
    assert n >= 1


def test_count_tokens_scales_with_length():
    short = count_tokens("claude-opus-4-5", text="hi")
    long = count_tokens("claude-opus-4-5", text="hi " * 500)
    assert long > short


def test_count_tokens_messages_form():
    n = count_tokens("claude-opus-4-5",
                     messages=[{"role": "user", "content": "hello world"}])
    assert n >= 1


def test_count_tokens_falls_back_when_litellm_unavailable(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def _fail(name, *a, **kw):
        if name == "litellm":
            raise ImportError("simulated missing litellm")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _fail)
    # Fallback heuristic: 400 chars / 4 = 100 tokens.
    assert count_tokens("claude-opus-4-5", text="x" * 400) == 100


def test_get_context_window_known_model():
    assert get_context_window("claude-opus-4-5") >= 100_000


def test_get_context_window_unknown_model_uses_fallback():
    assert get_context_window("not-a-real-model-xyz-9999") == token_guard._FALLBACK_CONTEXT_WINDOW


def test_compute_budget_formula():
    window = get_context_window("claude-opus-4-5")
    expected = int(window * DEFAULT_THRESHOLD) - DEFAULT_RESERVE_OUTPUT
    assert compute_budget("claude-opus-4-5") == expected


def test_compute_budget_custom_threshold():
    assert (compute_budget("claude-opus-4-5", threshold=0.5)
            < compute_budget("claude-opus-4-5", threshold=0.9))


def test_compute_budget_is_never_below_one():
    assert compute_budget("claude-opus-4-5", threshold=0.0001,
                          reserve_for_output=10_000_000) == 1
