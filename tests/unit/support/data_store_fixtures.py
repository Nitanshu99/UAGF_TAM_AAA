"""Shared fixtures for the aaa.data persistence-layer tests."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Redirect AAA_DATA_DIR to tmp_path for every test in the importing module."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path / "data"))
    return tmp_path / "data"
