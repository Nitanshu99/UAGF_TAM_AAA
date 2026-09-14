"""cgsa_ingest end-to-end: happy path, strict/non-strict, aggregation, verdicts."""
from __future__ import annotations

import copy

import pytest

from aaa.tools.cgsa_ingest import CGSAIngestError, IngestResult, cgsa_ingest
from tests.unit.support.cgsa_fixture import base_payload  # noqa: F401


def test_cgsa_ingest_happy_path(base_payload):  # noqa: F811
    """Valid fixture must ingest cleanly and populate key state_delta fields."""
    result = cgsa_ingest(base_payload)
    assert isinstance(result, IngestResult)
    assert result.schema_errors == []
    assert result.state_delta["cgsa_composite_maturity_score"] == pytest.approx(3.4, abs=0.01)
    assert result.state_delta["harmonised_standards_applied"] is True


def test_cgsa_ingest_strict_raises_on_invalid(base_payload):  # noqa: F811
    """cgsa_ingest(strict=True) must raise CGSAIngestError on invalid payload."""
    bad = copy.deepcopy(base_payload)
    del bad["metadata"]
    with pytest.raises(CGSAIngestError) as exc_info:
        cgsa_ingest(bad, strict=True)
    assert "schema_validation_failed" in str(exc_info.value)


def test_cgsa_ingest_non_strict_returns_errors(base_payload):  # noqa: F811
    """cgsa_ingest(strict=False) must return errors without raising."""
    bad = copy.deepcopy(base_payload)
    del bad["metadata"]
    assert len(cgsa_ingest(bad, strict=False).schema_errors) > 0


def test_cgsa_ingest_low_confidence_aggregation(base_payload):  # noqa: F811
    """Setting a control confidence < 0.6 must appear in low_confidence_controls."""
    payload = copy.deepcopy(base_payload)
    first_control = payload["domains"][0]["controls"][0]
    first_control["confidence"] = 0.4
    result = cgsa_ingest(payload)
    ids = [c["control_id"] for c in result.low_confidence_controls]
    assert first_control["control_id"] in ids


def test_cgsa_ingest_csp_failure_forces_fail(base_payload):  # noqa: F811
    """csp_satisfiable=False must force cgsa_phase5_verdict to 'FAIL'."""
    payload = copy.deepcopy(base_payload)
    payload["overall_scores"]["csp_satisfiable"] = False
    assert cgsa_ingest(payload).state_delta["cgsa_phase5_verdict"] == "FAIL"


def test_cgsa_ingest_risk_tier_match(base_payload):  # noqa: F811
    """Matching risk_tier (fixture=high) must set cgsa_risk_tier_match=True."""
    result = cgsa_ingest(base_payload, phase1_risk_tier="high")
    assert result.state_delta["cgsa_risk_tier_match"] is True


def test_cgsa_ingest_risk_tier_mismatch(base_payload):  # noqa: F811
    """Mismatched risk_tier must set cgsa_risk_tier_match=False."""
    result = cgsa_ingest(base_payload, phase1_risk_tier="limited")
    assert result.state_delta["cgsa_risk_tier_match"] is False
