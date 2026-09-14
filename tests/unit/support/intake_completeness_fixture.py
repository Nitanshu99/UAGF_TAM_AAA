"""Shared Stage B fixture helpers for the intake-completeness tests."""
from __future__ import annotations

import json
import pathlib

_STAGE_B_FIXTURE = (
    pathlib.Path(__file__).parents[3]
    / "scripts" / "fixtures" / "uci_german_credit" / "stage_b.json"
)


def load_stage_b() -> dict:
    """Load the UCI German Credit Stage B dossier as a mutable dict."""
    with _STAGE_B_FIXTURE.open() as f:
        return json.load(f)


def make_submission(stage_b: dict) -> dict:
    """Wrap a stage_b dict in a minimal ClientSubmission shape."""
    return {
        "stage_a": {"declared_modality": "tabular"},
        "stage_b": stage_b,
        "stage_c": None,
        "intake_completeness_score": 0.0,
    }
