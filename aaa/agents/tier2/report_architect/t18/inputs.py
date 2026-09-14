"""The values T18 is assembled from, read off the final declaration."""
from __future__ import annotations

from typing import Any, NamedTuple

from aaa.agents.tier2.report_architect.roadmap import remediation_roadmap
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION


class T18Inputs(NamedTuple):
    """What T18 reads off the declaration before it assembles anything."""

    ics: Any
    cs: Any
    rc: Any
    final_verdict: str
    blocking_findings: list
    positive_findings: list
    roadmap: list
    hitl: bool


def t18_inputs(decl: dict) -> T18Inputs:
    """Read the declaration into the values T18 is built from.

    :param decl: The final AuditState.
    :returns: The inputs, including the Q17 roadmap — the partner roadmap plus a
        step for every finding it does not cover.
    """
    blocking_findings = decl.get("blocking_findings", []) or []
    return T18Inputs(
        ics=decl.get("intake_completeness_score"),
        cs=decl.get("completeness_score"),
        rc=decl.get("regulatory_coverage_pct"),
        final_verdict=decl.get("final_verdict") or DISCLAIMER_OF_OPINION,
        blocking_findings=blocking_findings,
        positive_findings=decl.get("positive_findings", []) or [],
        roadmap=remediation_roadmap(decl.get("remediation_roadmap", []) or [],
                                    blocking_findings),
        hitl=bool(decl.get("hitl_required", False)),
    )


__all__ = ["T18Inputs", "t18_inputs"]
