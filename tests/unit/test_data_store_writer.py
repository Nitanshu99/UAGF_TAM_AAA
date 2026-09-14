"""Tests for the aaa.data.writer input-side persistence."""
from __future__ import annotations

import json

from tests.unit.support.data_store_fixtures import isolated_data_dir  # noqa: F401


class TestWriter:
    def test_save_engagement_creates_file(self):
        from aaa.data.models import EngagementRecord
        from aaa.data.paths import ENGAGEMENT_FILE, inputs_dir
        from aaa.data.writer import save_engagement

        save_engagement(EngagementRecord(
            engagement_id="eng-w1",
            provider_name="Acme",
            system_name="Bot",
            declared_risk_tier="high",
            cgsa_assessment_id=None,
            status="created",
        ))
        path = inputs_dir("eng-w1") / ENGAGEMENT_FILE
        assert path.exists()
        assert json.loads(path.read_text())["provider_name"] == "Acme"

    def test_save_intake_creates_file(self):
        from aaa.data.paths import INTAKE_FILE, inputs_dir
        from aaa.data.writer import save_intake

        save_intake("eng-w2", {"q1": "a"}, {"b1": "x"}, None)
        path = inputs_dir("eng-w2") / INTAKE_FILE
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["stage_a"] == {"q1": "a"}
        assert data["stage_c"] is None

    def test_save_uploaded_file_appends(self):
        from aaa.data.models import UploadedFileMeta
        from aaa.data.paths import FILES_META_FILE, inputs_dir
        from aaa.data.writer import save_uploaded_file

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
        records = json.loads((inputs_dir("eng-w3") / FILES_META_FILE).read_text())
        assert len(records) == 3
