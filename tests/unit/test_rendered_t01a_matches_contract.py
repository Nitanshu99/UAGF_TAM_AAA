"""The stored T01a — the form plus what triage_render derives — validates against its template.

Rendering added display labels, branch flags, the scope-gate verdict and the schema
version after validating the form, and the template described none of them, so
every stored T01a violated its own contract (T-20260913-019).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.platform.evidence.contract import artefact_schema_errors
from aaa.tools.triage_render import triage_render


@pytest.mark.parametrize("case", sorted(p.parent.name for p in Path("mock").glob("0[1-5]_*/stage_a.json")))
def test_the_rendered_triage_is_schema_valid(case: str) -> None:
    """Every tracked case's rendered Stage A is a valid T01a."""
    result = triage_render(json.loads(Path(f"mock/{case}/stage_a.json").read_text(encoding="utf-8")))
    assert result.is_valid, result.schema_errors
    assert artefact_schema_errors("T01a_stage_a_triage", result.rendered) == []
