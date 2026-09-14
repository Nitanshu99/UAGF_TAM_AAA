"""The fresh-embedding rule: a returning engagement never reuses old vectors."""
from __future__ import annotations

from typing import Any

import pytest

from aaa.tools.client_doc_ingest import freshness


class _FakeQdrant:
    """Minimal Qdrant stand-in recording which collections were dropped."""

    def __init__(self, existing: bool = True) -> None:
        self.existing = existing
        self.dropped: set[str] = set()
        self.deleted: list[str] = []

    def collection_exists(self, collection: str) -> bool:
        """Report whether *collection* is present, per collection."""
        return self.existing and collection not in self.dropped

    def delete_collection(self, collection_name: str) -> None:
        """Record the drop."""
        self.deleted.append(collection_name)
        self.dropped.add(collection_name)


@pytest.fixture(autouse=True)
def _clear_tracking() -> Any:
    """Each test starts as a fresh process would."""
    freshness.reset_tracking()
    yield
    freshness.reset_tracking()


def test_first_ingest_of_a_run_drops_the_previous_collection() -> None:
    """A returning customer's documents are assumed updated, so vectors go."""
    client = _FakeQdrant()
    assert freshness.reset_for_run(client, "client_docs_eng_01", "eng-01") is True
    assert client.deleted == ["client_docs_eng_01"]


def test_second_call_in_the_same_run_appends_instead_of_wiping() -> None:
    """Two callers share one run.

    ``client_doc_ingest`` is invoked by both the DocIntelligence agent and the
    IntakeValidator; resetting on the second call would delete the chunks the
    first had just written.
    """
    client = _FakeQdrant()
    freshness.reset_for_run(client, "client_docs_eng_01", "eng-01")
    assert freshness.reset_for_run(client, "client_docs_eng_01", "eng-01") is False
    assert client.deleted == ["client_docs_eng_01"]


def test_a_different_engagement_is_reset_independently() -> None:
    """One engagement's reset must not suppress another's."""
    client = _FakeQdrant()
    freshness.reset_for_run(client, "client_docs_eng_01", "eng-01")
    assert freshness.reset_for_run(client, "client_docs_eng_02", "eng-02") is True
    assert client.deleted == ["client_docs_eng_01", "client_docs_eng_02"]


def test_absent_collection_needs_no_drop() -> None:
    """A first-ever engagement has nothing to reset."""
    client = _FakeQdrant(existing=False)
    assert freshness.reset_for_run(client, "client_docs_new", "eng-new") is False
    assert not client.deleted


def test_a_reset_failure_does_not_abort_intake() -> None:
    """Worst case is keeping last run's vectors — the old behaviour."""
    class _Broken(_FakeQdrant):
        def collection_exists(self, collection: str) -> bool:
            raise RuntimeError("qdrant unreachable")

    assert freshness.reset_for_run(_Broken(), "client_docs_eng_01", "eng-01") is False
