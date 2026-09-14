"""Fix 30 (Q3) and the comparison-pair defect found while applying it.

**Fix 30.** `P4-FAIR-FOREIGN_WORKER` was raised *material* on a disparate-impact
ratio of 0.660 computed against a ten-row cohort, with no interval and no group
size anywhere in the artefact or the report. Every metric now carries a 95 %
interval and the denominators the number rests on.

**The pairing defect.** Both compute paths chose the two groups the four-fifths
ratio compares by *name*, not by outcome: aif360 — the path that actually runs —
took the alphabetically first label as privileged and the next as unprivileged,
so `age` reported 0.933 for `'18'` against `'19'`, and `personal_status`
reported 1.063 (PASS) when the worst pair was 0.671. Worse, aif360 binarises to
privileged-vs-everything-else, so on three or more groups the ratio was computed
against a pooled remainder while the artefact named a single unprivileged group.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier2.output_fairness.context import FairnessInputs
from aaa.agents.tier2.output_fairness.suite import run_fairness_suite
from aaa.agents.tier2.output_fairness.verdicts import apply_verdict_findings
from aaa.tools.disparate_impact import disparate_impact
from aaa.tools.disparate_impact.groups import comparison_pair
from aaa.tools.fairness_ci import CONFIDENCE_LEVEL, difference_ci, ratio_ci, wilson


def _column(spec: dict[str, tuple[int, int]]) -> tuple[list[int], list[str]]:
    """Build ``(y_pred, groups)`` from ``{group: (selected, n)}``."""
    y_pred: list[int] = []
    groups: list[str] = []
    for group, (selected, n) in spec.items():
        y_pred += [1] * selected + [0] * (n - selected)
        groups += [group] * n
    return y_pred, groups


# ── the comparison pair is chosen by outcome, not by spelling ────────────────

def test_the_pair_is_the_most_and_least_selected_groups():
    rates = {"18": 0.5, "19": 0.33, "40": 0.9, "41": 0.1}

    assert comparison_pair(rates, None) == ("40", "41")


def test_a_declared_privileged_group_still_wins():
    """The client's declaration is evidence about which group is advantaged."""
    rates = {"a": 0.9, "b": 0.5, "c": 0.2}

    assert comparison_pair(rates, "b") == ("b", "c")


def test_ties_break_on_the_name_so_the_pair_is_reproducible():
    rates = {"b": 0.5, "a": 0.5, "c": 0.1, "d": 0.1}

    assert comparison_pair(rates, None) == ("b", "c")
    assert comparison_pair(dict(reversed(list(rates.items()))), None) == ("b", "c")


def test_the_alphabetical_pair_no_longer_decides_the_ratio():
    """`'18'` vs `'19'` gave 0.933 while the real spread was 0.9 against 0.1."""
    y_pred, groups = _column({"18": (50, 100), "19": (33, 100),
                              "40": (90, 100), "41": (10, 100)})

    result = disparate_impact(y_pred=y_pred, sensitive_features=groups, positive_label=1)

    assert (result["privileged_group"], result["unprivileged_group"]) == ("40", "41")
    assert result["ratio"] == pytest.approx(0.111, abs=0.001)


def test_the_named_pair_is_the_pair_the_ratio_was_computed_over():
    """aif360 pooled every non-privileged row while naming one group (Q4-adjacent)."""
    y_pred, groups = _column({"a": (90, 100), "b": (10, 100), "c": (50, 100)})

    result = disparate_impact(y_pred=y_pred, sensitive_features=groups, positive_label=1)

    # 0.10 / 0.90 — b against a, not (b ∪ c) against a, which would be 0.333.
    assert result["ratio"] == pytest.approx(0.111, abs=0.001)
    assert (result["privileged_group"], result["unprivileged_group"]) == ("a", "b")


def test_a_two_group_attribute_is_unchanged():
    """`foreign_worker` was right by accident of spelling; it is now right by rule."""
    y_pred, groups = _column({"no": (7, 10), "yes": (140, 290)})

    result = disparate_impact(y_pred=y_pred, sensitive_features=groups, positive_label=1)

    assert (result["privileged_group"], result["unprivileged_group"]) == ("no", "yes")
    assert result["privileged_group_size"] == 10
    assert result["unprivileged_group_size"] == 290


# ── the interval estimators ──────────────────────────────────────────────────

def test_wilson_does_not_collapse_at_the_boundary():
    """A Wald interval reports ±0.000 at a rate of 1.0, which is where small
    cohorts land — six of `age`'s 45 sat at 0.0 and two at 1.0."""
    low, high = wilson(3, 3)

    assert low > 0.0 and high == 1.0
    assert high - low > 0.2


@pytest.mark.parametrize("n,expected_width", [(10, 0.6), (100, 0.2), (1000, 0.07)])
def test_the_interval_narrows_as_the_cohort_grows(n, expected_width):
    low, high = wilson(n // 2, n)

    assert (high - low) < expected_width


def test_a_ratio_on_ten_rows_is_reported_as_imprecise():
    """The Q3 case: 0.660 measured against ten rows does not exclude parity."""
    low, high = ratio_ci((140, 290), (7, 10))

    assert low is not None and high is not None
    assert low < 0.66 < high
    assert high > 1.0          # parity is inside the interval — no disparity shown


def test_a_ratio_on_a_real_sample_can_exclude_parity():
    low, high = ratio_ci((140, 290), (210, 290))

    assert high is not None and high < 1.0


def test_an_empty_group_yields_no_ratio_interval():
    assert ratio_ci((0, 0), (5, 10)) == (None, None)


def test_a_difference_interval_spans_zero_on_thin_cohorts():
    low, high = difference_ci((3, 5), (1, 5))

    assert low < 0.0 < high


# ── what the artefact and the finding now say ────────────────────────────────

def _inputs(spec: dict[str, tuple[int, int]]) -> FairnessInputs:
    y_pred, groups = _column(spec)
    return FairnessInputs(stage_b={}, task_type="classification", positive_label=1,
                          y_true=[i % 2 for i in range(len(y_pred))], y_pred=y_pred,
                          sensitive_map={"attr": groups},
                          sensitive_feature_names=["attr"])


def test_every_metric_carries_an_interval_and_its_denominators():
    suite = run_fairness_suite(_inputs({"a": (90, 150), "b": (40, 150)}))
    attr = suite.per_attribute[0]

    for metric in (attr["dp"], attr["eo"], attr["di"], attr["sg"]):
        interval = metric["confidence_interval"]
        assert interval["level"] == CONFIDENCE_LEVEL
        assert interval["low"] is not None and interval["high"] is not None
    assert {row["n"] for row in attr["dp"]["group_rates"]} == {150}
    assert all("n" in row for row in attr["eo"]["tpr_by_group"])
    assert attr["di"]["privileged_group_size"] == 150


def test_the_finding_quotes_the_interval_beside_the_number():
    """A ratio whose interval spans 1.0 must not read like an established disparity."""
    inp = _inputs({"a": (120, 150), "b": (60, 150)})
    suite = run_fairness_suite(inp)
    apply_verdict_findings(inp, suite)

    description = next(f["description"] for f in inp.findings
                       if f["finding_id"] == "P4-FAIR-ATTR")
    assert "95% CI" in description
    assert "smallest n=150" in description


def test_the_delivered_report_shows_the_interval():
    from aaa.agents.tier2.output_fairness.t12 import build_t12
    from aaa.tools.report_render.pdf.artefact_evidence import fairness_rows

    inp = _inputs({"a": (120, 150), "b": (60, 150)})
    suite = run_fairness_suite(inp)
    t12 = build_t12("eng-x", "tabular", inp, suite, None, "2026-09-02T00:00:00Z")

    rendered = dict(fairness_rows(t12))

    assert "95% CI" in rendered["Disparate impact"]
    assert "95% CI" in rendered["Demographic parity"]


def test_t12_still_validates_against_its_schema():
    from aaa.agents.tier2.output_fairness.t12 import build_t12
    from aaa.tools.template_render.logger import _load_schema, _validate_payload

    inp = _inputs({"a": (90, 150), "b": (40, 150)})
    suite = run_fairness_suite(inp)
    t12 = build_t12("eng-x", "tabular", inp, suite, None, "2026-09-02T00:00:00Z")

    assert _validate_payload(t12, _load_schema("T12_output_fairness_report"),
                             "T12_output_fairness_report") == []


def test_the_interval_decides_the_verdict():
    """0.44 over 150 + 150 rows: the whole interval lies below four-fifths — FAIL.

    Fix 30 left the verdict to the point estimate ("the interval reports; it does
    not gate"); 2026-09-14 made the interval the test.
    """
    suite = run_fairness_suite(_inputs({"a": (90, 150), "b": (40, 150)}))
    di = suite.per_attribute[0]["di"]

    assert di["confidence_interval"]["high"] < 0.8
    assert (di["verdict"], di["four_fifths_rule_passed"]) == ("FAIL", False)
    assert di["confidence_interval"]["groups"] == ["b", "a"]
