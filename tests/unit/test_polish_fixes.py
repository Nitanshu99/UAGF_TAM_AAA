"""Tests for the polish fixes (#3–#6) + the full audit-state API endpoint."""
from __future__ import annotations

from aaa.tools.eval_inputs import _infer_task_type

# ── #4 task_type inference ───────────────────────────────────────────────────

class _Reg:  # name contains "Regressor" → regression
    __class__ = type("RandomForestRegressor", (), {})


def test_infer_task_type_by_estimator_name():
    class IsolationForest: ...
    class RandomForestRegressor: ...
    class GradientBoostingClassifier: ...
    assert _infer_task_type(IsolationForest(), None) == "anomaly"
    assert _infer_task_type(RandomForestRegressor(), None) == "regression"


def test_infer_task_type_by_target_cardinality():
    class M: ...
    assert _infer_task_type(M(), [0, 1, 1, 0, 1]) == "classification"        # binary
    assert _infer_task_type(M(), list(range(200))) == "regression"          # many distinct


# ── #4 fairness NOT_APPLICABLE enum is allowed by the T12 schema ─────────────

def test_t12_schema_allows_not_applicable():
    from aaa.tools.template_render import _load_schema
    schema = _load_schema("T12_output_fairness_report")
    enum = schema["properties"]["overall_fairness_verdict"]["enum"]
    assert "NOT_APPLICABLE" in enum


# ── #3 report templates are exempt from HITL escalation ──────────────────────

def test_report_tids_constant():
    from aaa.agents.tier1.phases.verification import _REPORT_TIDS
    assert _REPORT_TIDS == {"T17_compliance_matrix", "T18_audit_report"}


# ── #6 data_dictionary flows from declared stage_b (no assumptions) ──────────

def test_declared_data_dictionary_yields_no_assumptions():
    from aaa.tools.data_dictionary import resolve_data_dictionary
    stage_b = {"data_dictionary": {
        "target_column": "credit_risk", "positive_label": 1,
        "sensitive_feature_columns": ["age", "foreign_worker"],
    }}
    dd = resolve_data_dictionary(stage_b, ["age", "foreign_worker", "amount", "credit_risk"])
    assert dd.target_column == "credit_risk"
    assert dd.target_explicit is True
    assert dd.sensitive_feature_columns == ["age", "foreign_worker"]
    assert dd.assumptions == []


# ── Part B: full audit-state endpoint (disk fallback) ────────────────────────

def test_audit_state_endpoint_shape(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from aaa.api.main import app
    client = TestClient(app)

    # 404 for an unknown engagement.
    assert client.get("/api/v1/engagements/nope-xyz/audit-state").status_code == 404

    # A known persisted engagement (written by earlier runs) returns the full state.
    import pathlib
    existing = list(pathlib.Path("data/customer").glob("*/*_audit_state.json"))
    if existing:
        eid = existing[0].name.replace("_audit_state.json", "")
        r = client.get(f"/api/v1/engagements/{eid}/audit-state")
        assert r.status_code == 200
        body = r.json()
        assert "compliance_matrix" in body and "engagement_id" in body
