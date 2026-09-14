"""evidence_truncate: basic contract and preserve-keys handling."""
from __future__ import annotations

import pytest

from aaa.tools.evidence_truncate import TruncationResult, truncate_payload
from tests.unit.support.evidence_truncate_fixture import _force_lexical  # noqa: F401


def test_returns_truncation_result_instance():
    result = truncate_payload({"a": "hello"}, query="hello",
                              model="claude-opus-4-5", max_tokens=10_000)
    assert isinstance(result, TruncationResult)


def test_non_dict_payload_raises():
    with pytest.raises(TypeError):
        truncate_payload("not a dict", query="x",  # type: ignore[arg-type]
                         model="claude-opus-4-5", max_tokens=100)


def test_empty_payload_returns_empty():
    result = truncate_payload({}, query="x", model="claude-opus-4-5", max_tokens=100)
    assert result.payload == {}
    assert result.kept_keys == []
    assert result.dropped_keys == []


def test_preserve_keys_are_always_kept():
    payload = {
        "engagement_id": "eng-001",
        "generated_at": "2026-01-01T00:00:00Z",
        "huge_blob": "x " * 5000,
    }
    result = truncate_payload(payload, query="anything", model="claude-opus-4-5",
                              max_tokens=50,
                              preserve_keys=("engagement_id", "generated_at"))
    assert "engagement_id" in result.payload
    assert "generated_at" in result.payload
    assert "huge_blob" in result.dropped_keys


def test_to_dict_marks_truncation_when_keys_dropped():
    result = truncate_payload({"engagement_id": "eng-001", "big": "x " * 5000},
                              query="anything", model="claude-opus-4-5",
                              max_tokens=10, preserve_keys=("engagement_id",))
    d = result.to_dict()
    assert d.get("_truncated") is True
    assert "big" in d.get("_dropped_keys", [])


def test_to_dict_does_not_mark_when_nothing_dropped():
    result = truncate_payload({"engagement_id": "eng-001", "small": "ok"},
                              query="anything", model="claude-opus-4-5",
                              max_tokens=10_000)
    d = result.to_dict()
    assert "_truncated" not in d
    assert "_dropped_keys" not in d
