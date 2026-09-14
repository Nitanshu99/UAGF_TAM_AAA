"""Unit tests for resolve_trace_sample — the trace_sample_uri intake loader."""
from __future__ import annotations

from aaa.agents.tier3.uagf_tam_l.trace_sample import resolve_trace_sample

_TRACES = [{"id": "t1", "steps": [{"type": "tool_call", "tool_name": "search", "depth": 1}]}]


class _FakeStore:
    """Resolves a fixed minio:// URI to a canned payload."""

    def __init__(self, payload):
        self._payload = payload

    def get_artefact(self, uri: str):
        """Return the canned payload regardless of URI."""
        return self._payload


def test_missing_uri_returns_empty_list():
    """No trace_sample_uri declared → empty list, no store call needed."""
    assert resolve_trace_sample({}, store=None) == []


def test_valid_json_array_uri_resolves():
    """A minio:// URI pointing at a JSON array of traces resolves it."""
    stage_b = {"trace_sample_uri": "minio://eng-1/trace_sample.json"}
    store = _FakeStore(_TRACES)
    assert resolve_trace_sample(stage_b, store) == _TRACES


def test_non_array_payload_is_ignored():
    """A URI resolving to a JSON object (not an array) is treated as no evidence."""
    stage_b = {"trace_sample_uri": "minio://eng-1/trace_sample.json"}
    store = _FakeStore({"id": "not-a-list"})
    assert resolve_trace_sample(stage_b, store) == []


def test_load_failure_is_fail_soft():
    """A store that raises never propagates — the caller gets an empty list."""
    class _BrokenStore:
        """Store stub whose get_artefact always raises."""

        def get_artefact(self, uri: str):
            """Simulate an unreachable backing store."""
            raise RuntimeError("minio unreachable")

    stage_b = {"trace_sample_uri": "minio://eng-1/trace_sample.json"}
    assert resolve_trace_sample(stage_b, _BrokenStore()) == []
