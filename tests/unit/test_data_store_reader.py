"""Tests for the aaa.data.reader load/list helpers."""
from __future__ import annotations

from tests.unit.support.data_store_fixtures import isolated_data_dir  # noqa: F401


class TestReader:
    def test_round_trip_engagement(self):
        from aaa.data.models import EngagementRecord
        from aaa.data.reader import load_engagement
        from aaa.data.writer import save_engagement

        save_engagement(EngagementRecord("eng-r1", "X", "Y", "minimal", None, "created"))
        loaded = load_engagement("eng-r1")
        assert loaded is not None
        assert loaded["system_name"] == "Y"

    def test_round_trip_intake(self):
        from aaa.data.reader import load_intake
        from aaa.data.writer import save_intake

        save_intake("eng-r2", {"k": "v"}, {"b": 1}, {"c": True})
        loaded = load_intake("eng-r2")
        assert loaded["stage_a"] == {"k": "v"}
        assert loaded["stage_c"] == {"c": True}

    def test_load_missing_returns_none(self):
        from aaa.data.reader import load_audit_result, load_engagement
        assert load_engagement("missing-xyz") is None
        assert load_audit_result("missing-xyz") is None

    def test_load_uploaded_files_empty(self):
        from aaa.data.reader import load_uploaded_files
        assert load_uploaded_files("no-files-eng") == []

    def test_list_results_filters_incomplete(self):
        from aaa.data import index as idx
        from aaa.data.reader import list_results

        idx.upsert({"engagement_id": "incomplete", "status": "created",
                    "created_at": "2025-01-01", "final_verdict": None})
        idx.upsert({"engagement_id": "done", "status": "completed",
                    "created_at": "2025-01-02", "final_verdict": "PASS"})
        ids = [r["engagement_id"] for r in list_results()]
        assert "done" in ids
        assert "incomplete" not in ids
