"""Contract: every CGSA fixture is valid JSON at schema_version 1.0.0."""
from __future__ import annotations

import json
import pathlib

import pytest

from aaa.tools.cgsa_ingest import schema_validate
from tests.contract.support.cgsa_contract import fixture_paths


@pytest.mark.parametrize("fixture_path", fixture_paths(), ids=lambda p: p.name)
def test_fixture_is_valid_json(fixture_path: pathlib.Path):
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{fixture_path.name} must be a JSON object"


@pytest.mark.parametrize("fixture_path", fixture_paths(), ids=lambda p: p.name)
def test_fixture_schema_version(fixture_path: pathlib.Path):
    payload = json.loads(fixture_path.read_text())
    assert payload.get("schema_version") == "1.0.0", (
        f"{fixture_path.name}: schema_version must be '1.0.0', "
        f"got {payload.get('schema_version')!r}")


@pytest.mark.parametrize("fixture_path", fixture_paths(), ids=lambda p: p.name)
def test_fixture_passes_schema_validate(fixture_path: pathlib.Path):
    payload = json.loads(fixture_path.read_text())
    errors = schema_validate(payload, "1.0.0")
    assert errors == [], (
        f"{fixture_path.name} failed schema_validate:\n"
        + "\n".join(f"  · {e}" for e in errors))
