"""evidence_truncate: relevance ranking and budget enforcement."""
from __future__ import annotations

from aaa.tools.evidence_truncate import truncate_payload
from tests.unit.support.evidence_truncate_fixture import _force_lexical  # noqa: F401


def test_relevant_key_kept_before_irrelevant_one():
    payload = {
        "risk_management": "Article 9 risk management lifecycle policy and review",
        "unrelated_metadata": "cafeteria menu lunch sandwich",
    }
    result = truncate_payload(payload, query="risk management article 9",
                              model="claude-opus-4-5", max_tokens=20)
    # Budget only fits one entry; relevant key must win.
    assert "risk_management" in result.kept_keys
    assert "unrelated_metadata" in result.dropped_keys


def test_ranking_is_deterministic_across_runs():
    payload = {f"k{i}": f"content body number {i}" for i in range(8)}
    first = truncate_payload(payload, query="content",
                             model="claude-opus-4-5", max_tokens=40)
    second = truncate_payload(payload, query="content",
                              model="claude-opus-4-5", max_tokens=40)
    assert first.kept_keys == second.kept_keys
    assert first.dropped_keys == second.dropped_keys


def test_budget_respected_final_tokens_within_limit():
    payload = {f"k{i}": "x " * 100 for i in range(20)}
    result = truncate_payload(payload, query="x",
                              model="claude-opus-4-5", max_tokens=200)
    assert result.final_tokens <= 200
