"""
Unit tests for aaa.tools.cgsa_ingest (§10.2).

Covers:
  - schema_validate: valid payload, missing top-level keys, version mismatch
  - _shallow_required_check: missing top-level key, missing handoff key
  - cgsa_ingest: happy path, strict error, non-strict error, low-confidence
    aggregation, CSP failure forces FAIL verdict, risk-tier cross-check

The base payload is loaded from the bundled UCI German Credit CGSA fixture
(scripts/fixtures/cgsa/uci-german-credit-001.json) which is known to be
schema-valid; individual tests mutate deep copies to isolate each case.
"""
from __future__ import annotations

import copy
import json
import pathlib
import pytest

from aaa.tools.cgsa_ingest import (
    CGSAIngestError,
    IngestResult,
    _shallow_required_check,
    cgsa_ingest,
    schema_validate,
)

# ---------------------------------------------------------------------------
# Base payload — loaded from the committed fixture so it always satisfies the
# CGSA JSON Schema (validated by the contract test suite).
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parents[2]
_FIXTURE = _REPO_ROOT / "scripts" / "fixtures" / "cgsa" / "uci-german-credit-001.json"


@pytest.fixture(scope="module")
def base_payload() -> dict:
    return json.loads(_FIXTURE.read_text())


# ── schema_validate ──────────────────────────────────────────────────────────


def test_schema_validate_valid_payload(base_payload):
    """Known-good UCI German Credit fixture must produce zero schema errors."""
    errors = schema_validate(base_payload, "1.0.0")
    assert errors == [], f"Expected no errors, got: {errors}"


def test_schema_validate_version_mismatch(base_payload):
    """Requesting a non-existent schema version must return a mismatch error."""
    errors = schema_validate(base_payload, "9.9.9")
    assert any("mismatch" in e for e in errors)


def test_schema_validate_missing_required_key(base_payload):
    """Remove a top-level required key and expect at least one error."""
    bad = copy.deepcopy(base_payload)
    del bad["metadata"]
    errors = schema_validate(bad, "1.0.0")
    assert len(errors) > 0


# ── _shallow_required_check ──────────────────────────────────────────────────


def test_shallow_required_check_valid(base_payload):
    """Valid fixture must produce no shallow-check errors."""
    errors = _shallow_required_check(base_payload)
    assert errors == []


def test_shallow_required_check_missing_top_level(base_payload):
    """Removing 'domains' must be detected by the shallow check."""
    bad = {k: v for k, v in base_payload.items() if k != "domains"}
    errors = _shallow_required_check(bad)
    assert any("domains" in e for e in errors)


def test_shallow_required_check_missing_handoff_key(base_payload):
    """Removing a required handoff key must surface in the shallow check."""
    bad = copy.deepcopy(base_payload)
    del bad["aaa_phase5_handoff"]["phase5_verdict"]
    errors = _shallow_required_check(bad)
    assert any("phase5_verdict" in e for e in errors)


def test_shallow_required_check_non_dict():
    """Non-dict payload must return a 'JSON object' error."""
    errors = _shallow_required_check("not a dict")  # type: ignore[arg-type]
    assert any("JSON object" in e for e in errors)


# ── cgsa_ingest ──────────────────────────────────────────────────────────────


def test_cgsa_ingest_happy_path(base_payload):
    """Valid fixture must ingest cleanly and populate key state_delta fields."""
    result = cgsa_ingest(base_payload)
    assert isinstance(result, IngestResult)
    assert result.schema_errors == []
    assert result.state_delta["cgsa_composite_maturity_score"] == pytest.approx(3.4, abs=0.01)
    assert result.state_delta["harmonised_standards_applied"] is True


def test_cgsa_ingest_strict_raises_on_invalid(base_payload):
    """cgsa_ingest(strict=True) must raise CGSAIngestError on invalid payload."""
    bad = copy.deepcopy(base_payload)
    del bad["metadata"]
    with pytest.raises(CGSAIngestError) as exc_info:
        cgsa_ingest(bad, strict=True)
    assert "schema_validation_failed" in str(exc_info.value)


def test_cgsa_ingest_non_strict_returns_errors(base_payload):
    """cgsa_ingest(strict=False) must return errors without raising."""
    bad = copy.deepcopy(base_payload)
    del bad["metadata"]
    result = cgsa_ingest(bad, strict=False)
    assert len(result.schema_errors) > 0


def test_cgsa_ingest_low_confidence_aggregation(base_payload):
    """Setting a control confidence < 0.6 must appear in low_confidence_controls."""
    payload = copy.deepcopy(base_payload)
    first_control = payload["domains"][0]["controls"][0]
    first_control["confidence"] = 0.4
    result = cgsa_ingest(payload)
    ids = [c["control_id"] for c in result.low_confidence_controls]
    assert first_control["control_id"] in ids


def test_cgsa_ingest_csp_failure_forces_fail(base_payload):
    """csp_satisfiable=False must force cgsa_phase5_verdict to 'FAIL'."""
    payload = copy.deepcopy(base_payload)
    payload["overall_scores"]["csp_satisfiable"] = False
    result = cgsa_ingest(payload)
    assert result.state_delta["cgsa_phase5_verdict"] == "FAIL"


def test_cgsa_ingest_risk_tier_match(base_payload):
    """Matching risk_tier (fixture=high) must set cgsa_risk_tier_match=True."""
    result = cgsa_ingest(base_payload, phase1_risk_tier="high")
    assert result.state_delta["cgsa_risk_tier_match"] is True


def test_cgsa_ingest_risk_tier_mismatch(base_payload):
    """Mismatched risk_tier must set cgsa_risk_tier_match=False."""
    result = cgsa_ingest(base_payload, phase1_risk_tier="limited")
    assert result.state_delta["cgsa_risk_tier_match"] is False
