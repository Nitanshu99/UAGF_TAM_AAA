"""Tests for Streamlit upload helper behavior without launching a browser."""
from __future__ import annotations

from aaa.platform.evidence import EvidenceStore
from aaa.ui import app
from aaa.ui.app import (
    _collect_stage_a,
    _collect_stage_b,
    _normalise_version,
    _parse_stage_b_metrics,
    _store_uploaded_file,
)


class _FakeUpload:
    name = "model.json"
    type = "application/json"

    @staticmethod
    def getvalue() -> bytes:
        return b'{"model": "demo"}'


def test_store_uploaded_file_returns_uri_for_stage_b_payload():
    store = EvidenceStore()
    uri = _store_uploaded_file(store, "eng-ui", "model_metadata_uri", _FakeUpload())
    assert uri and uri.startswith("minio://eng-ui/customer_uploads/model_metadata_uri")
    assert store.get_artefact(uri)["filename"] == "model.json"


def test_normalise_version_strips_common_v_prefix():
    assert _normalise_version("v2.1") == "2.1"
    assert _normalise_version(" V2.1.0 ") == "2.1.0"
    assert _normalise_version("release-2.1") == "release-2.1"


def test_collect_stage_a_normalises_version(monkeypatch):
    monkeypatch.setattr(
        app.st,
        "session_state",
        {
            "s3_a_provider_name": "FinClear GmbH",
            "s3_a_system_name": "CreditGuard",
            "s3_a_version": "v2.1",
            "s3_a_intended_purpose": "Credit scoring decision support for EU retail loan officers.",
            "s3_a_declared_modality": "tabular",
            "s3_a_declared_risk_tier": "high",
            "s3_a_declared_annex_iii_sections": ["5"],
        },
    )

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
    assert robustness == {"adversarial_accuracy_l_inf_0_01": 0.74, "psi_baseline_max": 0.04}


def test_collect_stage_b_splits_wrapped_metrics(monkeypatch):
    monkeypatch.setattr(
        app.st,
        "session_state",
        {
            "s3_b_accuracy_metrics_raw": (
                '{"accuracy_metrics":{"accuracy":0.935},'
                '"robustness_metrics":{"psi_baseline_max":0.04}}'
            ),
            "s3_b_lifecycle_change_log_raw": "v2.0 initial production release 2025-07-01\n"
            "v2.1 fairness recalibration 2026-01-10",
            "s3_b_harmonised_standards_raw": "ISO/IEC 42001:2023",
            "s3_b_other_standards_raw": "EBA/GL/2019/04",
        },
    )

    stage_b = _collect_stage_b()

    assert stage_b["accuracy_metrics"] == {"accuracy": 0.935}
    assert stage_b["robustness_metrics"] == {"psi_baseline_max": 0.04}
    assert stage_b["lifecycle_change_log"] == [
        "v2.0 initial production release 2025-07-01",
        "v2.1 fairness recalibration 2026-01-10",
    ]
