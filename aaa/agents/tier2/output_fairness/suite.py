"""The per-attribute fairness suite (steps 2–5)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.context import (
    FAIRNESS_VERDICT_ORDER,
    FairnessInputs,
    SuiteResult,
)
from aaa.agents.tier2.output_fairness.outcomes import _tested, _untested
from aaa.tools.demographic_parity import demographic_parity
from aaa.tools.disparate_impact import disparate_impact
from aaa.tools.equal_opportunity import equal_opportunity
from aaa.tools.fairness_groups import resolve_groups
from aaa.tools.subgroup_metrics import subgroup_metrics


def run_fairness_suite(inp: FairnessInputs) -> SuiteResult:
    """Run the fairness suite once per protected attribute.

    Tests *every* declared/inferred protected attribute (a real auditor does
    not stop at one).  Each attribute's cohorts are resolved first — a
    continuous column is binned, and a grouping too small to support a metric is
    refused rather than measured (fix 27, findings Q2/Q3).  The worst-performing
    tested attribute supplies the headline T12 detail and the overall worst-band
    verdict.

    :param inp: Resolved Phase 4 inputs.
    :returns: :class:`SuiteResult` with the worst attribute's metric details
        and a per-attribute breakdown used to raise named findings.
    """
    attributes: list[tuple[str, Any]] = []
    if inp.sensitive_map:
        attributes = list(inp.sensitive_map.items())
    elif inp.sensitive_features is not None:
        attributes = [("sensitive_feature", inp.sensitive_features)]

    per_attribute: list[dict[str, Any]] = []
    for name, groups in attributes:
        res = resolve_groups(name, list(groups))
        per_attribute.append(_tested(inp, res) if res.tested else _untested(res))

    if not per_attribute:
        return SuiteResult(dp=demographic_parity(), eo=equal_opportunity(),
                           di=disparate_impact(), sg=subgroup_metrics(),
                           overall_verdict="NOT_TESTED", sample_size=None, per_attribute=[])
    worst = max(per_attribute, key=lambda a: FAIRNESS_VERDICT_ORDER.index(a["verdict"]))
    # An attribute the suite refused carries the tools' empty stubs, whose sample
    # size is None; the evaluation set was still scored, and T12 reports its size.
    scored = len(inp.y_pred) if inp.y_pred is not None else 0
    sample_size = max((a["dp"].get("sample_size") or 0 for a in per_attribute),
                      default=0) or scored
    return SuiteResult(dp=worst["dp"], eo=worst["eo"], di=worst["di"], sg=worst["sg"],
                       overall_verdict=worst["verdict"], sample_size=sample_size or None,
                       per_attribute=per_attribute)
