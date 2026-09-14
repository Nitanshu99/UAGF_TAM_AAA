"""Fix 27 (Q2, Q3) — a metric is only computed over cohorts that can support it.

The part-2 run asserted a **material** non-conformity on `age`: a continuous
integer handed to the metric tools one group per distinct value, 45 cohorts from
300 rows, smallest n = 1.  Three of the four metrics returned exactly 1.0 — the
maximum each can take — while the artefact's own disparate-impact check passed
the same attribute.  The second material finding rested on a ten-row group.

Two rules, tested here: bin a continuous attribute before measuring it, and let
the interval — not a fixed minimum cohort size — decide whether a disparity can be
told from sampling noise (2026-09-14: the 30-row floor refused case 05 outright).
Only a grouping with a single cohort, which has nothing to compare, is declined.
"""
from __future__ import annotations

from collections import Counter

import pytest

# Fix 47 (R15): a Phase 4 evidence gap holds back the article this phase is
# contracted to evidence. Art. 15 §1 is accuracy/robustness/cybersecurity and
# was never one of them; Art. 9 is named by the findings but assessed by
# Phase 5, so it is not a gap Phase 4 may open.
from aaa.agents.tier2.output_fairness.articles import EVIDENCED_ARTICLES
from aaa.agents.tier2.output_fairness.context import FairnessInputs
from aaa.agents.tier2.output_fairness.suite import run_fairness_suite
from aaa.agents.tier2.output_fairness.t12 import build_t12
from aaa.agents.tier2.output_fairness.verdicts import apply_verdict_findings
from aaa.tools.fairness_groups import is_continuous, resolve_groups


def _ages(n: int = 300) -> list[int]:
    """A continuous age column shaped like the case's: many values, thin cohorts."""
    return [18 + (i * 7) % 45 for i in range(n)]


def _alternating(labels: list[str], counts: list[int]) -> list[str]:
    return [label for label, count in zip(labels, counts) for _ in range(count)]


def _inputs(**over: object) -> FairnessInputs:
    n = 300
    inp = FairnessInputs(
        stage_b={}, task_type="classification", positive_label=1,
        y_true=[i % 2 for i in range(n)], y_pred=[(i // 3) % 2 for i in range(n)],
        sensitive_map={"age": _ages(n)}, sensitive_feature_names=["age"])
    for key, value in over.items():
        setattr(inp, key, value)
    return inp


# ── binning a continuous attribute ───────────────────────────────────────────

def test_a_continuous_attribute_is_recognised_and_a_category_is_not():
    """Many numeric levels bin; a binary, a bool or a label does not."""
    assert is_continuous(_ages()) is True
    assert is_continuous(["yes", "no"] * 150) is False
    assert is_continuous([0, 1] * 150) is False          # a numeric binary is a category
    assert is_continuous([True, False] * 150) is False   # and so is a bool


def test_binning_replaces_one_cohort_per_value_with_populated_bands():
    """300 ages become five named quantile bands."""
    res = resolve_groups("age", _ages())

    assert res.binned is True
    assert res.tested is True
    assert res.group_count == 5
    # Bands name their observed range, so a reader sees the cohort not a bin index.
    assert all("-" in band for band in res.bands)


def test_binning_does_not_look_at_cohort_sizes():
    """70 rows are cut into quintiles like 300 are; the thin bands widen the interval."""
    res = resolve_groups("age", _ages(70))

    assert (res.group_count, res.tested) == (5, True)
    assert res.smallest_group_size < 30


def test_the_45_cohort_grouping_no_longer_reaches_the_metrics():
    """The Q2 measurement itself: 1.0 was a property of the cohort count."""
    inp = _inputs()

    suite = run_fairness_suite(inp)

    assert suite.dp["difference"] < 1.0
    assert len(suite.dp["group_rates"]) <= 5
    assert suite.per_attribute[0]["resolution"]["binned"] is True


# ── a small cohort is measured, and its interval decides ─────────────────────

@pytest.mark.parametrize("counts, smallest", [([290, 10], 10), ([159, 99, 27, 15], 15)])
def test_a_small_cohort_is_tested_not_refused(counts, smallest):
    """`foreign_worker` (290/10) and `personal_status` (smallest 15) as delivered."""
    labels = [f"g{i}" for i in range(len(counts))]
    res = resolve_groups("attr", _alternating(labels, counts))

    assert res.tested is True
    assert res.smallest_group_size == smallest
    assert f"smallest group n={smallest}." in res.reason


def test_a_single_group_is_refused_with_its_own_reason():
    """One cohort has nothing to compare, and says so."""
    res = resolve_groups("attr", ["yes"] * 300)

    assert res.tested is False
    assert "at least two cohorts" in res.reason


def test_a_sufficient_categorical_attribute_is_tested_unchanged():
    """A two-value category keeps its own labels."""
    values = _alternating(["a", "b"], [150, 150])
    res = resolve_groups("attr", values)

    assert (res.tested, res.binned, res.group_count) == (True, False, 2)
    assert res.labels == values


def test_an_undecidable_small_cohort_is_an_evidence_gap_and_never_a_breach():
    """290/10: the ratio's interval spans four-fifths, so neither verdict is asserted."""
    inp = _inputs(sensitive_map={"foreign_worker": _alternating(["yes", "no"], [290, 10])},
                  sensitive_feature_names=["foreign_worker"])

    suite = run_fairness_suite(inp)
    apply_verdict_findings(inp, suite)

    assert suite.overall_verdict == "INSUFFICIENT_EVIDENCE"
    assert [f["materiality"] for f in inp.findings] == ["possibly_material"]
    assert "establishes neither adverse impact nor its absence" in inp.findings[0]["description"]
    assert inp.insufficient == set(EVIDENCED_ARTICLES)


def test_a_single_group_attribute_reports_no_number_it_did_not_compute():
    """Nothing compared, so the tools' NOT_TESTED stubs and an evidence gap."""
    inp = _inputs(sensitive_map={"attr": ["a"] * 300}, sensitive_feature_names=["attr"])

    suite = run_fairness_suite(inp)
    skipped = apply_verdict_findings(inp, suite)

    for metric in (suite.dp, suite.eo, suite.di, suite.sg):
        assert metric["verdict"] == "NOT_TESTED"
        assert metric["sample_size"] is None
    # The evaluation set was still scored, and T12 still reports its size.
    assert suite.sample_size == 300
    assert inp.findings[0]["finding_id"] == "P4-FAIR-INSUFFICIENT-ATTR"
    assert "two or more cohorts" in (skipped or "")


def test_a_tested_attribute_beside_a_refused_one_still_yields_its_verdict():
    """A single-cohort attribute beside a real one leaves the article a gap."""
    inp = _inputs(sensitive_map={"age": _ages(), "site": ["one"] * 300},
                  sensitive_feature_names=["age", "site"])

    suite = run_fairness_suite(inp)
    apply_verdict_findings(inp, suite)

    verdicts = {a["attribute"]: a["verdict"] for a in suite.per_attribute}
    assert verdicts["site"] == "NOT_TESTED"
    assert verdicts["age"] != "NOT_TESTED"
    # The half that was assessed is reported; the half that was not is a gap.
    assert inp.insufficient == set(EVIDENCED_ARTICLES)


def test_an_unavailable_suite_still_reports_the_older_reason():
    """No predictions at all is a different failure from cohorts being too small."""
    inp = _inputs(sensitive_map={}, sensitive_feature_names=[], y_pred=None, y_true=None)

    suite = run_fairness_suite(inp)
    skipped = apply_verdict_findings(inp, suite)

    assert inp.findings[0]["finding_id"] == "P4-NOT-TESTED"
    # Inputs built directly carry no established cause; the reason must not invent one.
    assert "No scored predictions paired with protected attributes" in (skipped or "")


# ── what the client is told ──────────────────────────────────────────────────

def test_a_finding_carries_the_cohorts_its_number_was_measured_over():
    """The binned cohort count and the comparison count travel with the number."""
    inp = _inputs()

    suite = run_fairness_suite(inp)
    apply_verdict_findings(inp, suite)

    fairness = [f for f in inp.findings if f["finding_id"] == "P4-FAIR-AGE"]
    assert [f["materiality"] for f in fairness] == ["possibly_material"]
    assert "over 5 binned group(s), smallest n=" in fairness[0]["description"]
    assert "adjusted for 10 pairwise comparisons" in fairness[0]["description"]


def test_t12_carries_the_grouping_behind_every_metric():
    """group_resolution records binning, testability and the smallest cohort."""
    inp = _inputs(sensitive_map={"age": _ages(),
                                 "foreign_worker": _alternating(["yes", "no"], [290, 10])},
                  sensitive_feature_names=["age", "foreign_worker"])
    suite = run_fairness_suite(inp)

    t12 = build_t12("eng-x", "tabular", inp, suite, None, "2026-09-02T00:00:00Z")

    resolution = {r["attribute"]: r for r in t12["group_resolution"]}
    assert resolution["age"]["binned"] is True
    assert resolution["foreign_worker"]["tested"] is True
    assert resolution["foreign_worker"]["smallest_group_size"] == 10
    assert "minimum_group_size" not in resolution["age"]


def test_t12_validates_against_its_own_schema():
    """The payload the suite builds is schema-valid."""
    from aaa.tools.template_render.logger import _load_schema, _validate_payload

    inp = _inputs()
    suite = run_fairness_suite(inp)
    t12 = build_t12("eng-x", "tabular", inp, suite, None, "2026-09-02T00:00:00Z")

    assert not _validate_payload(t12, _load_schema("T12_output_fairness_report"),
                                 "T12_output_fairness_report")


def test_the_group_counts_reach_the_narrative_when_nothing_was_testable():
    """A single-cohort attribute's reason reaches skipped_reason and the narrative."""
    inp = _inputs(sensitive_map={"attr": ["a"] * 300}, sensitive_feature_names=["attr"])
    suite = run_fairness_suite(inp)
    skipped = apply_verdict_findings(inp, suite)
    t12 = build_t12("eng-x", "tabular", inp, suite, skipped, "2026-09-02T00:00:00Z")

    assert "two or more cohorts" in (t12["skipped_reason"] or "")
    assert "at least two cohorts to compare" in t12["fairness_narrative"]


def test_the_delivered_report_says_why_an_attribute_was_not_tested():
    """`Demographic parity — (NOT_TESTED)` with no reason is Q13 all over again."""
    from aaa.tools.report_render.pdf.artefact_evidence import fairness_rows

    inp = _inputs(sensitive_map={"age": _ages(),
                                 "foreign_worker": _alternating(["yes", "no"], [290, 10]),
                                 "site": ["one"] * 300},
                  sensitive_feature_names=["age", "foreign_worker", "site"])
    suite = run_fairness_suite(inp)
    t12 = build_t12("eng-x", "tabular", inp, suite, None, "2026-09-02T00:00:00Z")

    rendered = dict(fairness_rows(t12))

    assert "binned cohort(s)" in rendered["Cohorts · age"]
    assert "smallest n=10 — tested" in rendered["Cohorts · foreign_worker"]
    assert "not tested: fewer than two cohorts to compare" in rendered["Cohorts · site"]


def test_the_grouping_is_stable_across_runs():
    """A band assignment a client can reproduce; no sampling, no ordering effects."""
    first = resolve_groups("age", _ages())
    second = resolve_groups("age", list(reversed(_ages())))

    assert Counter(first.labels) == Counter(second.labels)
    assert first.bands == second.bands
