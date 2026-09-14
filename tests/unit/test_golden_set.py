"""Unit tests for resolve_golden_set — the golden_set_uri intake loader."""
from __future__ import annotations

from aaa.agents.tier3.uagf_tam_l.golden_set import _to_rows, resolve_golden_set

_ROWS = [
    {"question": "What colour is the sky?", "context": ["The sky is blue on a clear day."],
     "answer": "Blue", "expected": "The sky is blue."},
    {"question": "What is 2+2?", "context": ["Basic arithmetic."],
     "answer": "4", "expected": "4"},
]


class _FakeStore:
    """Resolves a fixed minio:// URI to a canned payload."""

    def __init__(self, payload):
        self._payload = payload

    def get_artefact(self, uri: str):
        """Return the canned payload regardless of URI."""
        return self._payload


def test_missing_uri_returns_none():
    """No golden_set_uri declared → None, no store call needed."""
    assert resolve_golden_set({}, store=None) is None


def test_valid_json_array_resolves_aligned_lists():
    """A minio:// URI pointing at a JSON array of Q&A rows resolves it."""
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    result = resolve_golden_set(stage_b, _FakeStore(_ROWS))
    assert result is not None
    questions, contexts, answers, expected = result
    assert questions == ["What colour is the sky?", "What is 2+2?"]
    assert contexts == [["The sky is blue on a clear day."], ["Basic arithmetic."]]
    assert answers == ["Blue", "4"]
    assert expected == ["The sky is blue.", "4"]


def test_csv_dataframe_payload_normalises_to_row_dicts():
    """A real pandas DataFrame (what a CSV upload deserialises to) normalises
    via to_dict("records") — the shape _row_tuple expects."""
    import pandas as pd
    df = pd.DataFrame([{"question": "Q1", "answer": "A1", "expected": "E1"}])
    assert _to_rows(df) == [{"question": "Q1", "answer": "A1", "expected": "E1"}]


def test_to_rows_ignores_non_dict_json_array_entries():
    """A JSON array with stray non-dict entries (e.g. a bad export) is tolerant."""
    assert _to_rows(["not a dict", {"question": "Q1"}, 42]) == [{"question": "Q1"}]


def test_string_context_is_wrapped_in_a_list():
    """A CSV-style single-string context column is wrapped, not iterated char-by-char."""
    rows = [{"question": "Q", "context": "single context string", "answer": "A", "expected": "E"}]
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    _q, contexts, _a, _e = resolve_golden_set(stage_b, _FakeStore(rows))
    assert contexts == [["single context string"]]


def test_a_row_without_a_system_answer_is_kept():
    """A reference set legitimately has no system answer yet.

    This asserted the opposite until 2026-09-11, and that is what dropped all
    55 rows of case 06's golden set: its export carries ``question`` and
    ``reference_answer`` because the system under test has not been run against
    it. Requiring ``answer`` made a real golden set unusable by construction,
    and the audit scored Art. 15 §1 on two hardcoded demo questions instead.
    The answer is kept as an empty string; ``run_golden_set`` reports the set
    as unscored rather than failing every row.
    """
    rows = [{"question": "Q1", "expected": "E1"},
            {"question": "Q2", "answer": "A2", "expected": "E2"}]
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    result = resolve_golden_set(stage_b, _FakeStore(rows))
    assert result == (["Q1", "Q2"], [[], []], ["", "A2"], ["E1", "E2"])


def test_a_row_without_a_question_or_reference_is_skipped():
    """Those two really are required — there is nothing to check against."""
    rows = [{"answer": "A1"}, {"question": "Q2", "answer": "A2", "expected": "E2"}]
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    assert resolve_golden_set(stage_b, _FakeStore(rows)) == (
        ["Q2"], [[]], ["A2"], ["E2"])


def test_an_export_wrapper_is_unwrapped():
    """Clients ship ``{name, count, items: [...]}``, not a bare array."""
    rows = {"name": "golden set", "count": 2, "items": [
        {"question": "Q1", "reference_answer": "E1"},
        {"question": "Q2", "reference_answer": "E2"}]}
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    questions, _, answers, expected = resolve_golden_set(stage_b, _FakeStore(rows))
    assert questions == ["Q1", "Q2"]
    assert expected == ["E1", "E2"]
    assert answers == ["", ""]


def test_reference_answer_is_recognised_as_the_expected_answer():
    """The alias case 06 actually uses."""
    rows = [{"question": "Q1", "reference_answer": "E1"}]
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    assert resolve_golden_set(stage_b, _FakeStore(rows))[3] == ["E1"]


def test_all_rows_incomplete_returns_none():
    """A file with zero usable rows returns None (fall back to demo defaults)."""
    rows = [{"question": "Q1"}]  # no reference to check against
    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    assert resolve_golden_set(stage_b, _FakeStore(rows)) is None


def test_load_failure_is_fail_soft():
    """A store that raises never propagates — the caller gets None."""
    class _BrokenStore:
        """Store stub whose get_artefact always raises."""

        def get_artefact(self, uri: str):
            """Simulate an unreachable backing store."""
            raise RuntimeError("minio unreachable")

    stage_b = {"golden_set_uri": "minio://eng-1/golden_set.json"}
    assert resolve_golden_set(stage_b, _BrokenStore()) is None
