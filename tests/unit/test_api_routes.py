"""Tests for modularised API routes (health, engagements, reports)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from aaa.api.main import app
    return TestClient(app)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "schema_version" in data


def test_schema_version(client):
    resp = client.get("/api/v1/schema-version")
    assert resp.status_code == 200
    assert "cgsa_schema_version" in resp.json()


def test_prometheus_metrics(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "aaa_" in resp.text or "python_" in resp.text


def test_create_and_get_engagement(client):
    payload = {
        "provider_name": "TestCo",
        "system_name": "TestSys",
        "declared_risk_tier": "limited",
    }
    resp = client.post("/api/v1/engagements", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    eid = data["engagement_id"]
    assert data["status"] == "created"

    resp2 = client.get(f"/api/v1/engagements/{eid}")
    assert resp2.status_code == 200
    assert resp2.json()["engagement_id"] == eid


def test_create_duplicate_engagement(client):
    payload = {
        "engagement_id": "test-duplicate-001",
        "provider_name": "X",
        "system_name": "Y",
        "declared_risk_tier": "minimal",
    }
    client.post("/api/v1/engagements", json=payload)
    resp = client.post("/api/v1/engagements", json=payload)
    assert resp.status_code == 409


def test_get_nonexistent_engagement(client):
    resp = client.get("/api/v1/engagements/does-not-exist-xyz")
    assert resp.status_code == 404


def test_list_engagements(client):
    resp = client.get("/api/v1/engagements")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_report_not_available(client):
    resp = client.get("/api/v1/engagements/no-such-eng/report")
    assert resp.status_code == 404


def test_submit_intake_unknown_engagement(client):
    body = {"stage_a": {}, "stage_b": {}}
    resp = client.post("/api/v1/engagements/nonexistent-99/intake", json=body)
    assert resp.status_code == 404
