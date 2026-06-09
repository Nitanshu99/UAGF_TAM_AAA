"""
Tests for the /api/v1/data/* endpoints and the end-to-end persistence flow.

Verifies that data written via POST /engagements, /intake, and /files
is readable back through GET /api/v1/data/engagements/{id}/input and /result.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path / "data"))
    # Also clear in-memory stores between tests
    from aaa.api import store as api_store
    api_store.ENGAGEMENTS.clear()
    api_store.INTAKE_PAYLOADS.clear()
    api_store.FINAL_STATES.clear()
    api_store.STORES.clear()


@pytest.fixture(scope="module")
def client():
    from aaa.api.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# List endpoints on empty store
# ---------------------------------------------------------------------------

def test_list_stored_engagements_empty(client):
    resp = client.get("/api/v1/data/engagements")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_stored_results_empty(client):
    resp = client.get("/api/v1/data/results")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# 404 for unknown engagement
# ---------------------------------------------------------------------------

def test_get_input_unknown(client):
    resp = client.get("/api/v1/data/engagements/no-such/input")
    assert resp.status_code == 404


def test_get_result_unknown(client):
    resp = client.get("/api/v1/data/engagements/no-such/result")
    assert resp.status_code == 404


def test_get_result_summary_unknown(client):
    resp = client.get("/api/v1/data/engagements/no-such/result/summary")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Engagement creation is persisted
# ---------------------------------------------------------------------------

def test_create_engagement_persists_to_data(client):
    resp = client.post("/api/v1/engagements", json={
        "provider_name": "Acme Corp",
        "system_name":   "CreditBot",
        "declared_risk_tier": "high",
    })
    assert resp.status_code == 201
    eid = resp.json()["engagement_id"]

    # Now read it back from the data store
    resp2 = client.get(f"/api/v1/data/engagements/{eid}/input/engagement")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["provider_name"] == "Acme Corp"
    assert data["system_name"] == "CreditBot"
    assert data["declared_risk_tier"] == "high"


def test_create_engagement_appears_in_list(client):
    resp = client.post("/api/v1/engagements", json={
        "provider_name": "Beta Inc",
        "system_name": "RiskAI",
        "declared_risk_tier": "limited",
    })
    eid = resp.json()["engagement_id"]

    list_resp = client.get("/api/v1/data/engagements")
    ids = [e["engagement_id"] for e in list_resp.json()]
    assert eid in ids


# ---------------------------------------------------------------------------
# Intake submission is persisted
# ---------------------------------------------------------------------------

def test_intake_submit_persists(client):
    # create
    eid = client.post("/api/v1/engagements", json={
        "provider_name": "X", "system_name": "Y", "declared_risk_tier": "minimal",
    }).json()["engagement_id"]

    # submit intake
    resp = client.post(f"/api/v1/engagements/{eid}/intake", json={
        "stage_a": {"declared_modality": "tabular", "declared_risk_tier": "minimal",
                    "intended_purpose": "credit scoring",
                    "deployment_context": "b2b", "provider_name": "X"},
        "stage_b": {"general_description": "A tabular model"},
    })
    assert resp.status_code == 200

    # read back
    resp2 = client.get(f"/api/v1/data/engagements/{eid}/input/intake")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["stage_a"]["declared_modality"] == "tabular"
    assert body["stage_c"] is None


# ---------------------------------------------------------------------------
# Uploaded files are persisted
# ---------------------------------------------------------------------------

def test_file_upload_persisted(client):
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

    files_resp = client.get(f"/api/v1/data/engagements/{eid}/input/files")
    assert files_resp.status_code == 200
    files = files_resp.json()
    assert len(files) == 1
    assert files[0]["filename"] == "risk.pdf"
    assert files[0]["role"] == "risk_management_file"
    assert files[0]["bytes_size"] == len(file_content)


# ---------------------------------------------------------------------------
# Full input view
# ---------------------------------------------------------------------------

def test_get_input_full_view(client):
    eid = client.post("/api/v1/engagements", json={
        "provider_name": "Corp", "system_name": "AI", "declared_risk_tier": "minimal",
    }).json()["engagement_id"]

    client.post(f"/api/v1/engagements/{eid}/intake", json={
        "stage_a": {"declared_modality": "tabular", "declared_risk_tier": "minimal",
                    "intended_purpose": "x", "deployment_context": "b2b", "provider_name": "Corp"},
        "stage_b": {"general_description": "desc"},
    })

    resp = client.get(f"/api/v1/data/engagements/{eid}/input")
    assert resp.status_code == 200
    body = resp.json()
    assert "engagement" in body
    assert "intake" in body
    assert "uploaded_files" in body
    assert body["engagement"]["provider_name"] == "Corp"
