"""A declared error-rate target is missed only when the rate's interval lies above it (T-20260914-050)."""
from __future__ import annotations

from aaa.agents.tier2.model_validator.targets import check_targets
from aaa.tools.metric_suite.binary import apply_binary


def test_a_rate_near_its_target_on_few_positives_is_not_established() -> None:
    """FNR 0.10 on 10 positives cannot place itself against a 0.05 target."""
    findings, positives = check_targets({"target_fnr": 0.05}, {"fnr": 0.10},
                                        {"tp": 9, "fn": 1, "fp": 0, "tn": 90})
    assert not positives
    assert [f["materiality"] for f in findings] == ["possibly_material"]
    assert "does not establish the declared target" in findings[0]["description"]


def test_without_counts_no_target_is_judged() -> None:
    """A point estimate alone decides nothing."""
    assert check_targets({"target_fnr": 0.02}, {"fnr": 0.269}) == ([], [])


def test_metric_suite_records_the_confusion_counts() -> None:
    """The counts the rates were computed from travel with them."""
    result = {"metrics": {}}
    apply_binary(result, [1, 1, 0, 0, 1], [1, 0, 0, 1, 1], 1)
    assert result["confusion"] == {"tp": 2, "fp": 1, "fn": 1, "tn": 1}
