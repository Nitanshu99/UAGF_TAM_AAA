"""Result summary printing for the mock-case runner."""
from __future__ import annotations

from typing import Any


def print_result(case: str, state: dict[str, Any]) -> None:
    """Print verdict, KPIs, compliance matrix and findings.

    :param case: Mock case folder name.
    :param state: Final audit state from the pipeline.
    """
    opinion = (state.get("auditor_opinion") or {}).get("opinion_type")
    print(f"\n=== {case} ===")
    print(f"final_verdict : {state.get('final_verdict')}")
    print(f"opinion       : {opinion}")
    print(f"KPIs          : intake={state.get('intake_completeness_score')} "
          f"completeness={state.get('completeness_score')} "
          f"coverage={state.get('regulatory_coverage_pct')}")
    print("compliance_matrix:")
    for article, verdict in sorted(state.get("compliance_matrix", {}).items()):
        print(f"  {article:14s} {verdict}")
    findings = state.get("blocking_findings", [])
    if findings:
        print(f"findings ({len(findings)}):")
        for f in findings:
            print(f"  [{f.get('materiality')}] {f.get('finding_id')}: "
                  f"{str(f.get('description'))[:90]}")
