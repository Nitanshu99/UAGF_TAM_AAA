"""cgsa_ingest schema_validate + _shallow_required_check paths."""
from __future__ import annotations

import copy

from aaa.tools.cgsa_ingest import _shallow_required_check, schema_validate
from tests.unit.support.cgsa_fixture import base_payload  # noqa: F401


def test_schema_validate_valid_payload(base_payload):  # noqa: F811
    """Known-good UCI German Credit fixture must produce zero schema errors."""
    errors = schema_validate(base_payload, "1.0.0")
    assert errors == [], f"Expected no errors, got: {errors}"


def test_schema_validate_version_mismatch(base_payload):  # noqa: F811
    """Requesting a non-existent schema version must return a mismatch error."""
    assert any("mismatch" in e for e in schema_validate(base_payload, "9.9.9"))


def test_schema_validate_missing_required_key(base_payload):  # noqa: F811
    """Remove a top-level required key and expect at least one error."""
    bad = copy.deepcopy(base_payload)
    del bad["metadata"]
    assert len(schema_validate(bad, "1.0.0")) > 0


def test_shallow_required_check_valid(base_payload):  # noqa: F811
    """Valid fixture must produce no shallow-check errors."""
    assert _shallow_required_check(base_payload) == []


def test_shallow_required_check_missing_top_level(base_payload):  # noqa: F811
    """Removing 'domains' must be detected by the shallow check."""
    bad = {k: v for k, v in base_payload.items() if k != "domains"}
    assert any("domains" in e for e in _shallow_required_check(bad))


def test_shallow_required_check_missing_handoff_key(base_payload):  # noqa: F811
    """Removing a required handoff key must surface in the shallow check."""
    bad = copy.deepcopy(base_payload)
    del bad["aaa_phase5_handoff"]["phase5_verdict"]
    assert any("phase5_verdict" in e for e in _shallow_required_check(bad))


def test_shallow_required_check_non_dict():
    """Non-dict payload must return a 'JSON object' error."""
    errors = _shallow_required_check("not a dict")  # type: ignore[arg-type]
    assert any("JSON object" in e for e in errors)
