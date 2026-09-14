"""Headline metric, declared F1 and declared error-rate targets (T-20260913-066, -069).

Case 03's anomaly detector was headlined by accuracy 0.972 while it missed 27 % of
anomalies against a declared false-negative target of 2 %; a declared F1 was
compared with macro F1, a different quantity.
"""
from __future__ import annotations

from aaa.agents.tier2.model_validator.declared import unverified_declared_finding
from aaa.agents.tier2.model_validator.metrics import diff_declared_metrics
from aaa.tools.metric_suite import metric_suite
from aaa.tools.metric_suite.binary import binary_metrics

_RARE_TRUE = [0] * 95 + [1] * 5
_RARE_PRED = [0] * 95 + [1, 1, 1, 0, 0]


def test_a_minority_positive_class_is_headlined_by_f1() -> None:
    """A minority positive class is headlined by F1."""
    result = metric_suite(_RARE_TRUE, _RARE_PRED, task="classification", positive_label=1)
    assert result["primary_metric"] == "f1" and result["primary_metric_value"] == 0.75
    assert result["metrics"]["accuracy"] == 0.98 and result["metrics"]["fnr"] == 0.4


def test_a_majority_positive_class_keeps_accuracy() -> None:
    """A majority positive class keeps accuracy."""
    result = metric_suite([1, 1, 1, 0], [1, 1, 0, 0], task="classification", positive_label=1)
    assert result["primary_metric"] == "accuracy"


def test_without_a_positive_label_or_a_binary_target_nothing_is_added() -> None:
    """Without a positive label or a binary target nothing is added."""
    assert "f1" not in metric_suite(_RARE_TRUE, _RARE_PRED, task="classification")["metrics"]
    assert binary_metrics([0, 1, 2], [0, 1, 2], 1) is None


def test_undefined_rates_are_null_not_zero() -> None:
    """Undefined rates are null not zero."""
    metrics = binary_metrics([0, 0], [0, 0], "0")
    assert metrics is not None and metrics["fnr"] == 0.0 and metrics["fpr"] is None


def test_declared_f1_is_compared_with_the_positive_class_f1() -> None:
    """Declared F1 is compared with the positive class F1."""
    computed = {"metrics": {"f1": 0.7647, "f1_macro": 0.7954}}
    _, positives = diff_declared_metrics({"f1_score": 0.7647}, computed,
                                         {"f1": (0.70, 0.82)})
    assert "the measured F1 0.765" in positives[0]["description"]


def test_declared_error_rate_targets_are_upper_bounds() -> None:
    """Declared error rate targets are upper bounds."""
    findings, positives = diff_declared_metrics(
        {"target_fnr": 0.02, "target_fpr": 0.10},
        {"metrics": {"fnr": 0.269, "fpr": 0.015},
         "confusion": {"tp": 19, "fn": 7, "fp": 9, "tn": 565}})
    assert [f["finding_id"] for f in findings] == ["P3-TARGET-FNR"]
    assert findings[0]["materiality"] == "material"
    assert [p["finding_id"] for p in positives] == ["P3-TARGET-FPR"]


def test_only_truly_unrecomputable_declarations_are_named() -> None:
    """Only truly unrecomputable declarations are named."""
    finding = unverified_declared_finding(
        {"accuracy_metrics": {"contamination": 0.05, "target_fnr": 0.02}},
        {"metrics": {"fnr": 0.269}}, "self_hosted")
    assert finding is not None
    assert "contamination" in finding["description"] and "target_fnr" not in finding["description"]
