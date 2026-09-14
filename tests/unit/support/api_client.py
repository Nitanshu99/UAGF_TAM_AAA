"""Shared FastAPI TestClient fixture for the API route tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """A TestClient bound to the FastAPI app."""
    from aaa.api.main import app
    return TestClient(app)
