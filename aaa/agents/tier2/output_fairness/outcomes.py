"""What a fairness suite reports for one attribute: tested, or explicitly not tested."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.aggregate import aggregate_verdict
from aaa.agents.tier2.output_fairness.context import FairnessInputs
from aaa.tools.demographic_parity import demographic_parity
from aaa.tools.disparate_impact import disparate_impact
from aaa.tools.equal_opportunity import equal_opportunity
from aaa.tools.fairness_ci import annotate_metrics
from aaa.tools.fairness_groups import GroupResolution
from aaa.tools.subgroup_metrics import subgroup_metrics


def _untested(res: GroupResolution) -> dict[str, Any]:
    """A per-attribute entry for a grouping with fewer than two cohorts to compare.

    The empty metric stubs are the tools' own ``NOT_TESTED`` results, so T12 and
    the report read a refused attribute exactly as they read an unavailable one:
    no number is reported that was not computed.
    """
    return {"attribute": res.attribute, "verdict": "NOT_TESTED",
            "dp": demographic_parity(), "eo": equal_opportunity(),
            "di": disparate_impact(), "sg": subgroup_metrics(),
            "resolution": res.as_dict()}
def _tested(inp: FairnessInputs, res: GroupResolution) -> dict[str, Any]:
    """Run the four metric families over one attribute's resolved cohorts."""
    groups = res.labels
    dp = demographic_parity(y_pred=inp.y_pred, sensitive_features=groups,
                            positive_label=inp.positive_label)
    eo = equal_opportunity(y_true=inp.y_true, y_pred=inp.y_pred,
                           sensitive_features=groups, positive_label=inp.positive_label)
    di = disparate_impact(y_pred=inp.y_pred, sensitive_features=groups,
                          privileged_group=inp.privileged_group,
                          positive_label=inp.positive_label)
    sg = subgroup_metrics(y_true=inp.y_true, y_pred=inp.y_pred,
                          sensitive_features=groups, positive_label=inp.positive_label)
    # Fix 30: the interval and the two denominators travel with the number, so a
    # ratio measured against a ten-row cohort cannot read like one measured on 300 —
    # and the verdict is reached from that interval, not from the point estimate.
    annotate_metrics(dp, eo, di, sg, y_true=inp.y_true, y_pred=inp.y_pred,
                     labels=groups, positive_label=inp.positive_label,
                     privileged_group=inp.privileged_group)
    verdict = aggregate_verdict([dp["verdict"], eo["verdict"], di["verdict"], sg["verdict"]])
    return {"attribute": res.attribute, "verdict": verdict,
            "dp": dp, "eo": eo, "di": di, "sg": sg, "resolution": res.as_dict()}


__all__ = ["_tested", "_untested"]
