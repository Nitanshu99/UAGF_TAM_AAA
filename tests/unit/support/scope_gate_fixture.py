"""Shared Stage A fixture loader for the scope_gate tests."""
from __future__ import annotations

import json
import pathlib

_FIXTURE = (
    pathlib.Path(__file__).parents[3]
    / "scripts" / "fixtures" / "uci_german_credit" / "stage_a.json"
)


def base_payload() -> dict:
    """Load the UCI German Credit Stage A fixture as a mutable dict."""
    with _FIXTURE.open() as f:
        return json.load(f)
