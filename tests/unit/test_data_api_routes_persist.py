"""Data API: engagement / intake / file writes are persisted and readable."""
from __future__ import annotations

from tests.unit.support.data_api_fixtures import client, isolated_data_dir  # noqa: F401


def test_create_engagement_persists_to_data(client):  # noqa: F811
    resp = client.post("/api/v1/engagements", json={
        "provider_name": "Acme Corp",
        "system_name": "CreditBot",
        "declared_risk_tier": "high",
    })
    assert resp.status_code == 201
    eid = resp.json()["engagement_id"]

    resp2 = client.get(f"/api/v1/data/engagements/{eid}/input/engagement")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["provider_name"] == "Acme Corp"
    assert data["system_name"] == "CreditBot"
    assert data["declared_risk_tier"] == "high"


def test_create_engagement_appears_in_list(client):  # noqa: F811
    resp = client.post("/api/v1/engagements", json={
        "provider_name": "Beta Inc", "system_name": "RiskAI",
        "declared_risk_tier": "limited",
    })
    eid = resp.json()["engagement_id"]
    ids = [e["engagement_id"] for e in client.get("/api/v1/data/engagements").json()]
    assert eid in ids


def test_intake_submit_persists(client):  # noqa: F811
    eid = client.post("/api/v1/engagements", json={
        "provider_name": "X", "system_name": "Y", "declared_risk_tier": "minimal",
    }).json()["engagement_id"]
    resp = client.post(f"/api/v1/engagements/{eid}/intake", json={
        "stage_a": {"declared_modality": "tabular", "declared_risk_tier": "minimal",
                    "intended_purpose": "credit scoring",
                    "deployment_context": "b2b", "provider_name": "X"},
        "stage_b": {"general_description": "A tabular model"},
    })
    assert resp.status_code == 200
    body = client.get(f"/api/v1/data/engagements/{eid}/input/intake").json()
    assert body["stage_a"]["declared_modality"] == "tabular"
    assert body["stage_c"] is None


