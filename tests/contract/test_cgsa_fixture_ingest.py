"""Contract: every CGSA fixture ingests strictly and populates §5.4 keys."""
from __future__ import annotations

import json
import pathlib

import pytest

from aaa.tools.cgsa_ingest import IngestResult, cgsa_ingest
from tests.contract.support.cgsa_contract import REQUIRED_STATE_KEYS, fixture_paths


@pytest.mark.parametrize("fixture_path", fixture_paths(), ids=lambda p: p.name)
def test_fixture_cgsa_ingest_strict(fixture_path: pathlib.Path):
    """cgsa_ingest(strict=True) must not raise on any bundled fixture."""
    payload = json.loads(fixture_path.read_text())
    assert isinstance(cgsa_ingest(payload, strict=True), IngestResult)


@pytest.mark.parametrize("fixture_path", fixture_paths(), ids=lambda p: p.name)
def test_fixture_state_delta_completeness(fixture_path: pathlib.Path):
    """All §5.4 state_delta keys must be present after ingestion."""
    payload = json.loads(fixture_path.read_text())
    result = cgsa_ingest(payload, strict=True)
    missing = [k for k in REQUIRED_STATE_KEYS if k not in result.state_delta]
    assert missing == [], f"{fixture_path.name}: state_delta missing keys: {missing}"
