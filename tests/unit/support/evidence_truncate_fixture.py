"""Shared autouse fixture for the evidence_truncate tests."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _force_lexical(monkeypatch):
    """Force the lexical (Jaccard) scorer for deterministic test output."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
