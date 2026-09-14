"""T09 keeps the provider's declared figures, unverified, apart from what was measured.

Case 06 declared seven ranking metrics and supplied no model; its model card said
``metrics: {}``, ``evaluation_sample_size: 0`` and nothing about the declaration
(T-20260913-013).
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from aaa.agents.tier2.model_validator.declared import declared_metrics, unverified_declared_finding
from aaa.agents.tier2.model_validator.t09 import build_t09
from aaa.tools.metric_suite import metric_suite
from tests.unit.support.case06_like_dossier import DECLARED_METRICS, STAGE_B, T01A

SCHEMA = json.loads(Path("templates/T09_model_card.json").read_text(encoding="utf-8"))
UNMEASURED = metric_suite(y_true=None, y_pred=None, task="classification")


def test_nothing_measured_is_null() -> None:
    """No predictions: no value and no sample size, rather than a sample of zero."""
    assert UNMEASURED["primary_metric_value"] is None
    assert UNMEASURED["evaluation_sample_size"] is None


def test_the_card_carries_the_declaration_and_validates() -> None:
    """Seven declared values, verified false, beside empty measured fields."""
    t09 = build_t09("eng-t", T01A, STAGE_B, "nlp", UNMEASURED, "2026-09-13T00:00:00Z",
                    declared=declared_metrics(STAGE_B))
    perf = t09["performance_metrics"]
    assert perf["declared_metrics"] == {"source": "stage_b.accuracy_metrics", "verified": False,
                                        "values": DECLARED_METRICS}
    assert perf["evaluation_sample_size"] is None and perf["primary_metric_value"] is None
    errors = [e.message for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(t09)]
    assert not errors, errors


def test_every_unrecomputed_declared_metric_is_named_with_its_reason() -> None:
    """Ranking metrics have no recomputation; a declared accuracy without predictions says so."""
    dossier = {"accuracy_metrics": {**DECLARED_METRICS, "accuracy": 0.9}}
    finding = unverified_declared_finding(dossier, UNMEASURED, "not_provided") or {}
    assert finding.get("finding_id") == "P3-DECLARED-UNVERIFIED"
    assert all(name in finding["description"] for name in DECLARED_METRICS)
    assert "accuracy (no model predictions; model_access_mode=not_provided)" in finding["description"]


def test_no_declaration_means_no_block_and_no_finding() -> None:
    """Silence is recorded as silence."""
    assert declared_metrics({}) is None
    assert unverified_declared_finding({}, UNMEASURED, None) is None
