"""API smoke test for upload → intake → run → report workflow."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["AAA_OFFLINE_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from aaa.api.main import app  # noqa: E402


FIXTURE_DIR = Path("scripts/fixtures/uci_german_credit")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_api_customer_upload_intake_run_report_shape():
    client = TestClient(app)
    engagement_id = "eng-api-upload-test"
    create = client.post(
        "/api/v1/engagements",
        json={
            "engagement_id": engagement_id,
            "provider_name": "Demo Provider",
            "system_name": "Demo System",
            "declared_risk_tier": "high",
        },
    )
    assert create.status_code == 201

    upload = client.post(
        f"/api/v1/engagements/{engagement_id}/files",
        data={"role": "risk_management_file_uri"},
        files={"file": ("risk.txt", b"risk policy evidence", "text/plain")},
    )
    assert upload.status_code == 200
    uri = upload.json()["uri"]

    stage_a = _load("stage_a.json")
    stage_b = _load("stage_b.json")
    stage_b["risk_management_file_uri"] = uri
    intake = client.post(
        f"/api/v1/engagements/{engagement_id}/intake",
        json={"stage_a": stage_a, "stage_b": stage_b, "stage_c": _load("stage_c.json")},
    )
    assert intake.status_code == 200

    run = client.post(f"/api/v1/engagements/{engagement_id}/run")
    assert run.status_code == 200
    report = client.get(f"/api/v1/engagements/{engagement_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["final_verdict"] in {"PASS", "PASS_WITH_OBSERVATIONS", "FAIL"}
    assert "t18_json_uri" in body
    assert "pdf_uri" in body