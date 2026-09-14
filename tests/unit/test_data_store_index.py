"""Tests for the aaa.data.index engagement index."""
from __future__ import annotations

from tests.unit.support.data_store_fixtures import isolated_data_dir  # noqa: F401


class TestIndex:
    def test_upsert_and_get(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "e1", "status": "created",
                    "created_at": "2025-01-01"})
        row = idx.get("e1")
        assert row is not None
        assert row["status"] == "created"

    def test_upsert_merges(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "e2", "status": "created",
                    "final_verdict": None, "created_at": "2025-01-01"})
        idx.upsert({"engagement_id": "e2", "status": "completed",
                    "final_verdict": "PASS"})
        row = idx.get("e2")
        assert row["status"] == "completed"
        assert row["final_verdict"] == "PASS"
        assert row["created_at"] == "2025-01-01"  # preserved from first upsert

    def test_list_all_newest_first(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "ea", "created_at": "2025-01-01",
                    "status": "created"})
        idx.upsert({"engagement_id": "eb", "created_at": "2025-06-01",
                    "status": "created"})
        ids = [r["engagement_id"] for r in idx.list_all()]
        assert ids.index("eb") < ids.index("ea")

    def test_get_missing_returns_none(self):
        from aaa.data import index as idx
        assert idx.get("does-not-exist-xyz") is None

    def test_delete(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "edel", "status": "created",
                    "created_at": "2025-01-01"})
        assert idx.delete("edel") is True
        assert idx.get("edel") is None
        assert idx.delete("edel") is False  # already gone
