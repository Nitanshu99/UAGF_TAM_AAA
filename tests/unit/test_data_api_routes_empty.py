"""Data API: empty-store listings and 404s for unknown engagements."""
from __future__ import annotations

from tests.unit.support.data_api_fixtures import client, isolated_data_dir  # noqa: F401


def test_list_stored_engagements_empty(client):  # noqa: F811
    resp = client.get("/api/v1/data/engagements")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_stored_results_empty(client):  # noqa: F811
    resp = client.get("/api/v1/data/results")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_input_unknown(client):  # noqa: F811
    assert client.get("/api/v1/data/engagements/no-such/input").status_code == 404


def test_get_result_unknown(client):  # noqa: F811
    assert client.get("/api/v1/data/engagements/no-such/result").status_code == 404


def test_get_result_summary_unknown(client):  # noqa: F811
    resp = client.get("/api/v1/data/engagements/no-such/result/summary")
    assert resp.status_code == 404
