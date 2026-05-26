"""
Unit tests for aaa.tools.evidence_truncate.

Covers:
  - preserve_keys are always retained, even when over budget
  - dropped entries are recorded in _dropped_keys with _truncated marker
  - ranking is deterministic across runs (same input → same kept_keys order)
  - more-relevant entries are kept before less-relevant entries
  - non-dict payload raises TypeError
  - empty payload returns empty TruncationResult
"""
from __future__ import annotations

import os

import pytest

from aaa.tools.evidence_truncate import TruncationResult, truncate_payload


@pytest.fixture(autouse=True)
def _force_offline(monkeypatch):
    """Force the offline (Jaccard) scorer for deterministic test output."""
    monkeypatch.setenv("AAA_OFFLINE_MODE", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Reload the module-level _OFFLINE flag.
    from aaa.tools import evidence_truncate

    monkeypatch.setattr(evidence_truncate, "_OFFLINE", True)


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------

def test_returns_truncation_result_instance():
    result = truncate_payload(
        {"a": "hello"}, query="hello",
        model="claude-opus-4-5", max_tokens=10_000,
    )
    assert isinstance(result, TruncationResult)


def test_non_dict_payload_raises():
    with pytest.raises(TypeError):
        truncate_payload(
            "not a dict", query="x",  # type: ignore[arg-type]
            model="claude-opus-4-5", max_tokens=100,
        )


def test_empty_payload_returns_empty():
    result = truncate_payload(
        {}, query="x", model="claude-opus-4-5", max_tokens=100,
    )
    assert result.payload == {}
    assert result.kept_keys == []
    assert result.dropped_keys == []


# ---------------------------------------------------------------------------
# Preserve keys
# ---------------------------------------------------------------------------

def test_preserve_keys_are_always_kept():
    payload = {
        "engagement_id": "eng-001",
        "generated_at": "2026-01-01T00:00:00Z",
        "huge_blob": "x " * 5000,
    }
    result = truncate_payload(
        payload, query="anything",
        model="claude-opus-4-5", max_tokens=50,
        preserve_keys=("engagement_id", "generated_at"),
    )
    assert "engagement_id" in result.payload
    assert "generated_at" in result.payload
    assert "huge_blob" in result.dropped_keys


def test_to_dict_marks_truncation_when_keys_dropped():
    payload = {
        "engagement_id": "eng-001",
        "big": "x " * 5000,
    }
    result = truncate_payload(
        payload, query="anything",
        model="claude-opus-4-5", max_tokens=10,
        preserve_keys=("engagement_id",),
    )
    d = result.to_dict()
    assert d.get("_truncated") is True
    assert "big" in d.get("_dropped_keys", [])


def test_to_dict_does_not_mark_when_nothing_dropped():
    payload = {"engagement_id": "eng-001", "small": "ok"}
    result = truncate_payload(
        payload, query="anything",
        model="claude-opus-4-5", max_tokens=10_000,
    )
    d = result.to_dict()
    assert "_truncated" not in d
    assert "_dropped_keys" not in d


# ---------------------------------------------------------------------------
# Relevance ranking
# ---------------------------------------------------------------------------

def test_relevant_key_kept_before_irrelevant_one():
    payload = {
        "risk_management": "Article 9 risk management lifecycle policy and review",
        "unrelated_metadata": "cafeteria menu lunch sandwich",
    }
    result = truncate_payload(
        payload, query="risk management article 9",
        model="claude-opus-4-5", max_tokens=20,
    )
    # Budget only fits one entry; relevant key must win.
    assert "risk_management" in result.kept_keys
    assert "unrelated_metadata" in result.dropped_keys


def test_ranking_is_deterministic_across_runs():
    payload = {f"k{i}": f"content body number {i}" for i in range(8)}
    first = truncate_payload(
        payload, query="content",
        model="claude-opus-4-5", max_tokens=40,
    )
    second = truncate_payload(
        payload, query="content",
        model="claude-opus-4-5", max_tokens=40,
    )
    assert first.kept_keys == second.kept_keys
    assert first.dropped_keys == second.dropped_keys


def test_budget_respected_final_tokens_within_limit():
    payload = {f"k{i}": "x " * 100 for i in range(20)}
    result = truncate_payload(
        payload, query="x",
        model="claude-opus-4-5", max_tokens=200,
    )
    assert result.final_tokens <= 200
