"""Shared fixtures for the /api/v1/data/* route tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Redirect AAA_DATA_DIR to tmp_path and clear the in-memory API stores."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path / "data"))
    from aaa.api import store as api_store
    api_store.ENGAGEMENTS.clear()
    api_store.INTAKE_PAYLOADS.clear()
    api_store.FINAL_STATES.clear()
    api_store.STORES.clear()


@pytest.fixture(scope="module")
def client():
    """A FastAPI TestClient bound to the app."""
    from aaa.api.main import app
    return TestClient(app)
