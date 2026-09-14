"""Data API: file uploads persist and the full input view aggregates them."""
from __future__ import annotations

from tests.unit.support.data_api_fixtures import client, isolated_data_dir  # noqa: F401


def test_file_upload_persisted(client):  # noqa: F811
    eid = client.post("/api/v1/engagements", json={
        "provider_name": "Z", "system_name": "DocBot", "declared_risk_tier": "high",
    }).json()["engagement_id"]
    file_content = b"PDF bytes here"
    resp = client.post(
        f"/api/v1/engagements/{eid}/files",
        data={"role": "risk_management_file"},
        files={"file": ("risk.pdf", file_content, "application/pdf")},
    )
    assert resp.status_code == 200
    files = client.get(f"/api/v1/data/engagements/{eid}/input/files").json()
    assert len(files) == 1
    assert files[0]["filename"] == "risk.pdf"
    assert files[0]["role"] == "risk_management_file"
    assert files[0]["bytes_size"] == len(file_content)


def test_get_input_full_view(client):  # noqa: F811
    eid = client.post("/api/v1/engagements", json={
        "provider_name": "Corp", "system_name": "AI", "declared_risk_tier": "minimal",
    }).json()["engagement_id"]
    client.post(f"/api/v1/engagements/{eid}/intake", json={
        "stage_a": {"declared_modality": "tabular", "declared_risk_tier": "minimal",
                    "intended_purpose": "x", "deployment_context": "b2b",
                    "provider_name": "Corp"},
        "stage_b": {"general_description": "desc"},
    })
    body = client.get(f"/api/v1/data/engagements/{eid}/input").json()
    assert "engagement" in body
    assert "intake" in body
    assert "uploaded_files" in body
    assert body["engagement"]["provider_name"] == "Corp"
