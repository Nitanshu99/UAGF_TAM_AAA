"""Health, schema-version and Prometheus-metrics endpoints."""
from __future__ import annotations

from tests.unit.support.api_client import client  # noqa: F401


def test_healthz(client):  # noqa: F811
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "schema_version" in data


def test_schema_version(client):  # noqa: F811
    resp = client.get("/api/v1/schema-version")
    assert resp.status_code == 200
    assert "cgsa_schema_version" in resp.json()


def test_prometheus_metrics(client):  # noqa: F811
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "aaa_" in resp.text or "python_" in resp.text
