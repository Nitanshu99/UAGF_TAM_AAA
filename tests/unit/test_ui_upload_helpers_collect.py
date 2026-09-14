"""Streamlit Stage A/B collection helpers (session-state driven)."""
from __future__ import annotations

from aaa.ui import app
from aaa.ui.app import _collect_stage_a, _collect_stage_b, _parse_stage_b_metrics


def test_collect_stage_a_normalises_version(monkeypatch):
    monkeypatch.setattr(app.st, "session_state", {
        "s3_a_provider_name": "FinClear GmbH",
        "s3_a_system_name": "CreditGuard",
        "s3_a_version": "v2.1",
        "s3_a_intended_purpose": "Credit scoring decision support for EU loan officers.",
        "s3_a_declared_modality": "tabular",
        "s3_a_declared_risk_tier": "high",
        "s3_a_declared_annex_iii_sections": ["5"],
    })
    assert _collect_stage_a()["version"] == "2.1"


def test_parse_stage_b_metrics_unwraps_fixture_shape():
    raw = """
    {
      "accuracy_metrics": {"accuracy": 0.935, "auc_roc": 0.9819, "f1_score": 0.9312},
      "robustness_metrics": {"adversarial_accuracy_l_inf_0_01": 0.74, "psi_baseline_max": 0.04}
    }
    """
    accuracy, robustness = _parse_stage_b_metrics(raw)
    assert accuracy == {"accuracy": 0.935, "auc_roc": 0.9819, "f1_score": 0.9312}
    assert robustness == {"adversarial_accuracy_l_inf_0_01": 0.74,
                          "psi_baseline_max": 0.04}


def test_collect_stage_b_splits_wrapped_metrics(monkeypatch):
    monkeypatch.setattr(app.st, "session_state", {
        "s3_b_accuracy_metrics_raw": (
            '{"accuracy_metrics":{"accuracy":0.935},'
            '"robustness_metrics":{"psi_baseline_max":0.04}}'
        ),
        "s3_b_lifecycle_change_log_raw": "v2.0 initial production release 2025-07-01\n"
        "v2.1 fairness recalibration 2026-01-10",
        "s3_b_harmonised_standards_raw": "ISO/IEC 42001:2023",
        "s3_b_other_standards_raw": "EBA/GL/2019/04",
    })
    stage_b = _collect_stage_b()
    assert stage_b["accuracy_metrics"] == {"accuracy": 0.935}
    assert stage_b["robustness_metrics"] == {"psi_baseline_max": 0.04}
    assert stage_b["lifecycle_change_log"] == [
        "v2.0 initial production release 2025-07-01",
        "v2.1 fairness recalibration 2026-01-10",
    ]


def test_ranking_metrics_keep_their_blocks_and_nothing_is_dropped_silently():
    """T-20260913-028: a flat merge filed an operational ratio as accuracy."""
    import json

    from aaa.ui.wizard.metric_check import discarded_metrics
    from aaa.ui.wizard.parsing import parse_stage_b_metrics

    accuracy = {"precision_at_5": 0.58, "ndcg_at_5": 0.71}
    robustness = {"latency_p95_ms": 380, "filter_reduction_ratio": 0.8}
    wrapped = json.dumps({"accuracy_metrics": accuracy, "robustness_metrics": robustness})
    assert parse_stage_b_metrics(wrapped) == (accuracy, {**robustness, "latency_p95_ms": 380.0})
    assert discarded_metrics(wrapped) == []
    flat = json.dumps({**accuracy, **robustness})
    assert discarded_metrics(flat) == ["latency_p95_ms"]
