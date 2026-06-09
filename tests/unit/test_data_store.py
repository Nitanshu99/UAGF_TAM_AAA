"""
Tests for the aaa.data persistence layer.

Covers:
- paths helpers (inputs_dir, results_dir, index_path)
- index (upsert, get, list_all, delete)
- writer (save_engagement, save_intake, save_uploaded_file, save_result)
- reader (load_*, list_*)
- data API routes via FastAPI TestClient
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures — redirect all data/ writes to a temporary directory
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Redirect AAA_DATA_DIR to tmp_path for every test."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path / "data"))
    # Reset module-level cached paths if any
    return tmp_path / "data"


@pytest.fixture(scope="module")
def client():
    from aaa.api.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------

class TestPaths:
    def test_inputs_dir(self, isolated_data_dir):
        from aaa.data.paths import inputs_dir
        p = inputs_dir("eng-001")
        assert p == isolated_data_dir / "inputs" / "eng-001"

    def test_results_dir(self, isolated_data_dir):
        from aaa.data.paths import results_dir
        p = results_dir("eng-001")
        assert p == isolated_data_dir / "results" / "eng-001"

    def test_index_path(self, isolated_data_dir):
        from aaa.data.paths import index_path
        assert index_path() == isolated_data_dir / "index.json"


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------

class TestIndex:
    def test_upsert_and_get(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "e1", "status": "created", "created_at": "2025-01-01"})
        row = idx.get("e1")
        assert row is not None
        assert row["status"] == "created"

    def test_upsert_merges(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "e2", "status": "created", "final_verdict": None, "created_at": "2025-01-01"})
        idx.upsert({"engagement_id": "e2", "status": "completed", "final_verdict": "PASS"})
        row = idx.get("e2")
        assert row["status"] == "completed"
        assert row["final_verdict"] == "PASS"
        assert row["created_at"] == "2025-01-01"  # preserved from first upsert

    def test_list_all_newest_first(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "ea", "created_at": "2025-01-01", "status": "created"})
        idx.upsert({"engagement_id": "eb", "created_at": "2025-06-01", "status": "created"})
        rows = idx.list_all()
        ids = [r["engagement_id"] for r in rows]
        assert ids.index("eb") < ids.index("ea")

    def test_get_missing_returns_none(self):
        from aaa.data import index as idx
        assert idx.get("does-not-exist-xyz") is None

    def test_delete(self):
        from aaa.data import index as idx
        idx.upsert({"engagement_id": "edel", "status": "created", "created_at": "2025-01-01"})
        assert idx.delete("edel") is True
        assert idx.get("edel") is None
        assert idx.delete("edel") is False  # already gone


# ---------------------------------------------------------------------------
# writer
# ---------------------------------------------------------------------------

class TestWriter:
    def test_save_engagement_creates_file(self):
        from aaa.data.writer import save_engagement
        from aaa.data.models import EngagementRecord
        from aaa.data.paths import inputs_dir, ENGAGEMENT_FILE

        rec = EngagementRecord(
            engagement_id="eng-w1",
            provider_name="Acme",
            system_name="Bot",
            declared_risk_tier="high",
            cgsa_assessment_id=None,
            status="created",
        )
        save_engagement(rec)
        path = inputs_dir("eng-w1") / ENGAGEMENT_FILE
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["provider_name"] == "Acme"

    def test_save_intake_creates_file(self):
        from aaa.data.writer import save_intake
        from aaa.data.paths import inputs_dir, INTAKE_FILE

        save_intake("eng-w2", {"q1": "a"}, {"b1": "x"}, None)
        path = inputs_dir("eng-w2") / INTAKE_FILE
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["stage_a"] == {"q1": "a"}
        assert data["stage_c"] is None

    def test_save_uploaded_file_appends(self):
        from aaa.data.writer import save_uploaded_file
        from aaa.data.models import UploadedFileMeta
        from aaa.data.paths import inputs_dir, FILES_META_FILE

        for i in range(3):
            save_uploaded_file(UploadedFileMeta(
                engagement_id="eng-w3",
                filename=f"doc{i}.pdf",
                role="risk_management_file",
                content_type="application/pdf",
                bytes_size=1000 + i,
                sha256="abc",
                uri=f"minio://eng-w3/doc{i}.pdf",
            ))
        path = inputs_dir("eng-w3") / FILES_META_FILE
        records = json.loads(path.read_text())
        assert len(records) == 3

    def test_save_result_creates_all_four_files(self):
        from aaa.data.writer import save_result
        from aaa.data.paths import (
            results_dir, AUDIT_RESULT_FILE,
            ARTEFACTS_FILE, FINDINGS_FILE, COMPLIANCE_MATRIX_FILE,
        )

        final_state: dict[str, Any] = {
            "final_verdict": "PASS",
            "intake_completeness_score": 0.92,
            "completeness_score": 0.95,
            "regulatory_coverage_pct": 93.0,
            "material_findings_count": 0,
            "possibly_material_findings_count": 1,
            "auditor_opinion": "Satisfactory",
            "art43_decision": {"procedure": "internal_control", "rationale": "ok"},
            "blocking_findings": [],
            "positive_findings": [{"id": "pf1"}],
            "remediation_roadmap": [],
            "compliance_matrix": {"Art.5": "PASS", "Art.10": "PASS"},
            "phase_artefacts": {"T02_system_card": {"uri": "mem://eng-w4/T02"}},
        }
        save_result("eng-w4", final_state)
        rdir = results_dir("eng-w4")
        for fname in [AUDIT_RESULT_FILE, ARTEFACTS_FILE, FINDINGS_FILE, COMPLIANCE_MATRIX_FILE]:
            assert (rdir / fname).exists(), f"{fname} not created"
        result = json.loads((rdir / AUDIT_RESULT_FILE).read_text())
        assert result["final_verdict"] == "PASS"


# ---------------------------------------------------------------------------
# reader
# ---------------------------------------------------------------------------

class TestReader:
    def test_round_trip_engagement(self):
        from aaa.data.writer import save_engagement
        from aaa.data.reader import load_engagement
        from aaa.data.models import EngagementRecord

        rec = EngagementRecord("eng-r1", "X", "Y", "minimal", None, "created")
        save_engagement(rec)
        loaded = load_engagement("eng-r1")
        assert loaded is not None
        assert loaded["system_name"] == "Y"

    def test_round_trip_intake(self):
        from aaa.data.writer import save_intake
        from aaa.data.reader import load_intake

        save_intake("eng-r2", {"k": "v"}, {"b": 1}, {"c": True})
        loaded = load_intake("eng-r2")
        assert loaded["stage_a"] == {"k": "v"}
        assert loaded["stage_c"] == {"c": True}

    def test_load_missing_returns_none(self):
        from aaa.data.reader import load_engagement, load_audit_result
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
        results = list_results()
        ids = [r["engagement_id"] for r in results]
        assert "done" in ids
        assert "incomplete" not in ids

    def test_load_full_result(self):
        from aaa.data.writer import save_result
        from aaa.data.reader import load_full_result

        save_result("eng-r3", {
            "final_verdict": "FAIL",
            "intake_completeness_score": 0.6,
            "completeness_score": 0.5,
            "regulatory_coverage_pct": 40.0,
            "material_findings_count": 2,
            "possibly_material_findings_count": 0,
            "auditor_opinion": None,
            "art43_decision": None,
            "blocking_findings": [{"id": "bf1"}],
            "positive_findings": [],
            "remediation_roadmap": [{"action": "fix data"}],
            "compliance_matrix": {"Art.5": "PENDING"},
            "phase_artefacts": {},
        })
        full = load_full_result("eng-r3")
        assert full is not None
        assert full["final_verdict"] == "FAIL"
        assert "findings" in full
        assert "compliance_matrix" in full
        assert "artefacts" in full
