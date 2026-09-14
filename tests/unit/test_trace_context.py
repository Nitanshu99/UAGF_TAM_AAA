"""Unit tests for the engagement-id contextvar and session-metadata helper."""
from __future__ import annotations

from aaa.observability.trace_context import (
    bind_engagement_id,
    current_engagement_id,
    with_session_metadata,
)


def test_unbound_by_default():
    """Outside any binding, current_engagement_id() is None."""
    assert current_engagement_id() is None


def test_bind_and_restore():
    """The binding is scoped to the with-block and restores afterward."""
    with bind_engagement_id("eng-01"):
        assert current_engagement_id() == "eng-01"
    assert current_engagement_id() is None


def test_nested_bindings_restore_outer_value():
    """Nested bindings restore the outer value on exit, not None."""
    with bind_engagement_id("outer"):
        with bind_engagement_id("inner"):
            assert current_engagement_id() == "inner"
        assert current_engagement_id() == "outer"


def test_with_session_metadata_injects_when_bound():
    """Bound engagement id adds session_id + tags to the call kwargs."""
    with bind_engagement_id("eng-01"):
        kwargs = with_session_metadata({"model": "gpt-5"}, "ModelValidator")
    assert kwargs["metadata"] == {"session_id": "eng-01", "tags": ["ModelValidator"]}


def test_with_session_metadata_noop_when_unbound():
    """No binding → kwargs pass through unchanged (no metadata key added)."""
    kwargs = with_session_metadata({"model": "gpt-5"}, "ModelValidator")
    assert "metadata" not in kwargs


def test_caller_metadata_keys_win_over_defaults():
    """Caller-supplied metadata values are never clobbered by the defaults."""
    with bind_engagement_id("eng-01"):
        kwargs = with_session_metadata(
            {"model": "gpt-5", "metadata": {"session_id": "custom", "extra": 1}},
            "ModelValidator")
    assert kwargs["metadata"] == {"session_id": "custom", "tags": ["ModelValidator"], "extra": 1}
