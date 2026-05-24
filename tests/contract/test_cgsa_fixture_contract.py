"""
Contract tests — every JSON fixture under scripts/fixtures/cgsa/ must:

  1. Be parseable as JSON.
  2. Carry schema_version == "1.0.0".
  3. Pass schema_validate with zero errors.
  4. Be ingested by cgsa_ingest (strict=True) without raising.
  5. Produce an IngestResult whose state_delta contains the mandatory §5.4 keys.

These tests act as the offline guard for the nightly s4_contract.yml gate:
if a fixture diverges from the vendored schema the CI run fails here first.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from aaa.tools.cgsa_ingest import IngestResult, cgsa_ingest, schema_validate

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_FIXTURE_DIR = _REPO_ROOT / "scripts" / "fixtures" / "cgsa"

# The §5.4 state_delta keys that every IngestResult must populate.
_REQUIRED_STATE_KEYS = (
    "cgsa_payload",
    "cgsa_schema_version",
    "cgsa_composite_maturity_score",
    "cgsa_composite_maturity_label",
    "cgsa_eu_ai_act_coverage_pct",
    "cgsa_csp_satisfiable",
    "cgsa_governance_verdict",
    "cgsa_phase5_verdict",
    "cgsa_phase5_narrative",
    "cgsa_blocking_findings",
    "cgsa_positive_findings",
    "cgsa_low_confidence_controls",
    "cgsa_recommended_follow_up",
    "cgsa_risk_tier_match",
    "harmonised_standards_applied",
)


def _fixture_ids():
    """Collect all *.json files under the cgsa fixture directory."""
    return sorted(_FIXTURE_DIR.glob("*.json"))


@pytest.mark.parametrize("fixture_path", _fixture_ids(), ids=lambda p: p.name)
def test_fixture_is_valid_json(fixture_path: pathlib.Path):
    content = fixture_path.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert isinstance(payload, dict), f"{fixture_path.name} must be a JSON object"


@pytest.mark.parametrize("fixture_path", _fixture_ids(), ids=lambda p: p.name)
def test_fixture_schema_version(fixture_path: pathlib.Path):
    payload = json.loads(fixture_path.read_text())
    assert payload.get("schema_version") == "1.0.0", (
        f"{fixture_path.name}: schema_version must be '1.0.0', "
        f"got {payload.get('schema_version')!r}"
    )


@pytest.mark.parametrize("fixture_path", _fixture_ids(), ids=lambda p: p.name)
def test_fixture_passes_schema_validate(fixture_path: pathlib.Path):
    payload = json.loads(fixture_path.read_text())
    errors = schema_validate(payload, "1.0.0")
    assert errors == [], (
        f"{fixture_path.name} failed schema_validate:\n"
        + "\n".join(f"  · {e}" for e in errors)
    )


@pytest.mark.parametrize("fixture_path", _fixture_ids(), ids=lambda p: p.name)
def test_fixture_cgsa_ingest_strict(fixture_path: pathlib.Path):
    """cgsa_ingest(strict=True) must not raise on any bundled fixture."""
    payload = json.loads(fixture_path.read_text())
    result = cgsa_ingest(payload, strict=True)
    assert isinstance(result, IngestResult)


@pytest.mark.parametrize("fixture_path", _fixture_ids(), ids=lambda p: p.name)
def test_fixture_state_delta_completeness(fixture_path: pathlib.Path):
    """All §5.4 state_delta keys must be present after ingestion."""
    payload = json.loads(fixture_path.read_text())
    result = cgsa_ingest(payload, strict=True)
    missing = [k for k in _REQUIRED_STATE_KEYS if k not in result.state_delta]
    assert missing == [], (
        f"{fixture_path.name}: state_delta missing keys: {missing}"
    )
