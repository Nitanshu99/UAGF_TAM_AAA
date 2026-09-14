"""No model or data test may report a number it did not measure (T-20260913-061..063).

Fallbacks, empty-input stubs and hard-coded values used to reach the audit as
measurements: "0.0 % missing" for a dataset never loaded, column variances as a
model's feature importances, ``sample_count: 1`` for PII never counted, toxicity
scores of 1.0 / 0.0 from a keyword list, a PSI of 0.0 for a feature never binned
and an interval of (-1, 1) around an empty cohort. Unmeasured is ``None``.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

import pandas as pd
import pytest

from aaa.agents.tier2.data_auditor.analysis import run_analysis
from aaa.agents.tier2.data_auditor.t07 import build_t07
from aaa.platform.evidence.contract import artefact_schema_errors
from aaa.tools.class_balance import class_balance
from aaa.tools.data_profile import data_profile
from aaa.tools.demographic_parity import demographic_parity
from aaa.tools.disparate_impact import disparate_impact
from aaa.tools.drift_test.psi import _numeric_psi
from aaa.tools.equal_opportunity import equal_opportunity
from aaa.tools.fairness_ci import difference_ci, difference_decision, wilson
from aaa.tools.gradcam_explain import gradcam_explain
from aaa.tools.lime_explain import lime_explain
from aaa.tools.metric_suite import metric_suite
from aaa.tools.missingness_scan import missingness_scan
from aaa.tools.pii_scan import _scan_keyword, pii_scan
from aaa.tools.robustness_probe import robustness_probe
from aaa.tools.shap_explain import shap_explain
from aaa.tools.subgroup_metrics import subgroup_metrics
from aaa.tools.toxicity_classifier import _compute_python, toxicity_classifier

#: Numbers that are configuration or counts of what actually ran (zero is then true).
_ALLOWED = {"threshold", "threshold_used", "imbalance_threshold", "epsilons", "level",
            "sample_size", "flagged_count", "total_probes", "successful_attacks", "n"}
_EMPTY = pd.DataFrame()

TOOLS: dict[str, Callable[[], Any]] = {
    "class_balance": lambda: class_balance(_EMPTY, target_column="label"),
    "missingness_scan": lambda: missingness_scan(_EMPTY),
    "data_profile": lambda: data_profile(_EMPTY),
    "pii_scan": lambda: pii_scan(_EMPTY),
    "toxicity_classifier": toxicity_classifier,
    "subgroup_metrics": subgroup_metrics,
    "demographic_parity": demographic_parity,
    "disparate_impact": disparate_impact,
    "equal_opportunity": equal_opportunity,
    "metric_suite": metric_suite,
    "robustness_probe": robustness_probe,
    "shap_explain": lambda: shap_explain(model=None, X=pd.DataFrame({"a": [1.0, 2.0, 9.0]})),
    "lime_explain": lambda: lime_explain(model=None, X=pd.DataFrame({"a": [1.0, 2.0, 9.0]})),
}


def _numbers(node: Any, key: str = "") -> list[str]:
    """Every numeric leaf outside the allow-list, as ``key=value``."""
    if isinstance(node, dict):
        return [n for k, v in node.items() for n in _numbers(v, str(k))]
    if isinstance(node, list):
        return [n for v in node for n in _numbers(v, key)]
    if isinstance(node, (int, float)) and not isinstance(node, bool) and key not in _ALLOWED:
        return [f"{key}={node}"]
    return []


@pytest.mark.parametrize("tool", sorted(TOOLS))
def test_a_tool_given_nothing_reports_no_measurement(tool: str) -> None:
    """With no evidence, every measurement field is null — whatever the tool."""
    assert _numbers(TOOLS[tool]()) == []


def test_phase_2_without_a_dataset_reports_nulls_that_validate() -> None:
    """The stand-in frame's zeros no longer reach T07 as the provider's data."""
    ctx = run_analysis(SimpleNamespace(store=None), {}, {"target_column": "label"})
    t07 = build_t07("eng", ctx["profile_result"], ctx["miss_result"], ctx["balance_result"],
                    ctx["pii_result"], ctx["verdict"], "2026-09-13T00:00:00Z")
    assert ctx["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert t07["dataset_summary"]["num_rows"] is None
    assert t07["missingness"]["overall_missingness_pct"] is None
    assert t07["class_balance"]["imbalance_detected"] is None
    assert t07["pii_scan"]["pii_detected"] is None
    assert "Missingness overall: not measured" in t07["quality_narrative"]
    assert artefact_schema_errors("T07_data_quality_report", t07) == []


def test_the_column_name_screen_counts_nothing_and_proves_no_absence() -> None:
    """A name match is an observation; no match is not "no PII"."""
    hit = _scan_keyword(pd.DataFrame({"email": ["x"], "income": [1]}), "en")
    assert hit["pii_detected"] is True
    assert all(e["sample_count"] is None for e in hit["entities_found"])
    assert _scan_keyword(pd.DataFrame({"income": [1]}), "en")["pii_detected"] is None


def test_a_keyword_screen_writes_no_toxicity_score() -> None:
    """Keyword hits flag; they do not score, and silence is not a PASS."""
    clean = _compute_python(["a neutral summary"], [0])
    assert clean["verdict"] == "NOT_TESTED" and clean["entries"][0]["toxicity_score"] is None
    flagged = _compute_python(["that group is inferior"], [0])
    assert flagged["flagged_count"] == 1 and flagged["verdict"] != "PASS"
    assert "threshold" not in clean and "threshold" not in flagged


def test_an_unscored_sample_records_no_toxicity_threshold() -> None:
    """T-20260914-060: nothing scored means no cut-off was applied, so none is written."""
    empty = toxicity_classifier(predictions=None)
    assert empty["verdict"] == "NOT_TESTED" and empty["tool"] is None and "threshold" not in empty


def test_a_near_constant_reference_still_shows_a_shift() -> None:
    """No quantile bins is no reason to report PSI 0.0."""
    assert _numeric_psi([0.0] * 50, [0.0] * 50, 10) == 0.0
    assert _numeric_psi([0.0] * 50, [5.0] * 50, 10) > 0.2


def test_an_empty_or_undefined_cohort_has_no_interval() -> None:
    """No hard-coded widest interval, and no undefined rate ranked as zero."""
    assert wilson(0, 0) == (None, None)
    assert difference_ci((3, 5), (0, 0)) == (None, None)
    # A cohort with no trials (no positives, say) has no rate and is not compared.
    assert difference_decision({"a": (1, 2), "b": (0, 0)}) is None


def test_fairness_tools_report_no_rate_they_could_not_compute() -> None:
    """No positives is no TPR, and one group has no parity — never 0.0 / 1.0."""
    from aaa.tools.demographic_parity.compute.python import _compute_python as dp_python
    from aaa.tools.equal_opportunity.compute.python import _compute_python as eo_python

    eo = eo_python([1, 0, 0, 0], [1, 0, 1, 0], ["a", "a", "b", "b"], 1)
    assert eo["tpr_by_group"][1]["true_positive_rate"] is None and eo["difference"] is None
    dp = dp_python([1, 0], ["a", "a"], 1)
    assert (dp["difference"], dp["ratio"]) == (None, None)


def test_grad_cam_that_cannot_run_returns_no_stub_maps() -> None:
    """A failed Grad-CAM leaves no placeholder heatmap, only its reason."""
    reasons: list[str] = []
    assert not gradcam_explain(model=object(), images=[[0.0]], reasons=reasons)
    assert reasons and "Grad-CAM could not run" in reasons[0]


def test_a_label_examination_that_did_not_run_says_exactly_why() -> None:
    """Case 03 had dataset and target; only protected attributes were undeclared."""
    from aaa.tools.label_disparity import label_disparity

    frame = pd.DataFrame({"anomaly_label": [0, 1], "x": [1.0, 2.0]})
    reason = label_disparity(frame, "anomaly_label", 1, [])["reason"]
    assert reason == "not examined: no protected attribute declared, so there are no groups to compare"
    assert label_disparity(None, "t", 1, ["a"])["reason"] == "not examined: no dataset was loaded"
    assert "'target' is not in the dataset" in label_disparity(frame, "target", 1, ["x"])["reason"]


def test_declared_special_category_data_is_not_reported_as_none() -> None:
    """Case 04: present=true beside 'Categories: none' and 'review not applicable'."""
    from aaa.agents.tier2.data_auditor.t08 import build_t08

    unscanned = build_t08("eng", True, {"analyser_engine": None}, False, "2026-09-13T00:00:00Z")
    assert "not identified" in unscanned["compliance_narrative"]
    assert "no dataset was scanned" in unscanned["compliance_narrative"]
    assert "not applicable" not in unscanned["compliance_narrative"]
    absent = build_t08("eng", False, {}, False, "2026-09-13T00:00:00Z")
    assert absent["compliance_narrative"].endswith("review not applicable.")


def test_a_continuous_target_has_no_class_balance() -> None:
    """Case 02: a forecaster's sales column was counted as 92 classes, 'severe' imbalance."""
    frame = pd.DataFrame({"sales": [float(i) * 1.37 for i in range(200)], "store": [1, 2] * 100})
    result = class_balance(frame, target_column="sales")
    assert result["class_distribution"] == [] and result["imbalance_detected"] is None
    assert result["imbalance_severity"] is None and result["target_column"] == "sales"
    labels = class_balance(pd.DataFrame({"y": [0] * 90 + [1] * 10}), target_column="y")
    assert labels["imbalance_detected"] is True
