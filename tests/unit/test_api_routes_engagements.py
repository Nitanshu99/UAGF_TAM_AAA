"""Engagement CRUD, report, and intake route behaviour."""
from __future__ import annotations

from tests.unit.support.api_client import client  # noqa: F401


def test_create_and_get_engagement(client):  # noqa: F811
    resp = client.post("/api/v1/engagements", json={
        "provider_name": "TestCo", "system_name": "TestSys",
        "declared_risk_tier": "limited",
    })
    assert resp.status_code == 201
    data = resp.json()
    eid = data["engagement_id"]
    assert data["status"] == "created"
    resp2 = client.get(f"/api/v1/engagements/{eid}")
    assert resp2.status_code == 200
    assert resp2.json()["engagement_id"] == eid


def test_create_duplicate_engagement(client):  # noqa: F811
    payload = {"engagement_id": "test-duplicate-001", "provider_name": "X",
               "system_name": "Y", "declared_risk_tier": "minimal"}
    client.post("/api/v1/engagements", json=payload)
    assert client.post("/api/v1/engagements", json=payload).status_code == 409


def test_get_nonexistent_engagement(client):  # noqa: F811
    assert client.get("/api/v1/engagements/does-not-exist-xyz").status_code == 404


def test_list_engagements(client):  # noqa: F811
    resp = client.get("/api/v1/engagements")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_report_not_available(client):  # noqa: F811
    assert client.get("/api/v1/engagements/no-such-eng/report").status_code == 404


def test_submit_intake_unknown_engagement(client):  # noqa: F811
    resp = client.post("/api/v1/engagements/nonexistent-99/intake",
                       json={"stage_a": {}, "stage_b": {}})
    assert resp.status_code == 404
