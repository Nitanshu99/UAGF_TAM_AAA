"""Shared CGSA base-payload fixture loaded from the committed fixture file."""
from __future__ import annotations

import json
import pathlib

import pytest

_FIXTURE = (
    pathlib.Path(__file__).parents[3]
    / "scripts" / "fixtures" / "cgsa" / "uci-german-credit-001.json"
)


@pytest.fixture(scope="module")
def base_payload() -> dict:
    """The known schema-valid UCI German Credit CGSA payload."""
    return json.loads(_FIXTURE.read_text())
