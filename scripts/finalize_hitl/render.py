"""FINAL T17 / T18 re-rendering from the resolved audit state."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def render_final_reports(state: dict[str, Any],
                         engagement_id: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Re-render T17 / T18 from the resolved state (builders are pure).

    :param state: Resolved audit state after human decisions were applied.
    :param engagement_id: Fallback engagement identifier.
    :returns: ``(t17, t18, now_iso)``.
    """
    from aaa.agents.tier2.report_architect.t17 import build_t17
    from aaa.agents.tier2.report_architect.t18 import build_t18

    now = datetime.now(timezone.utc).isoformat()
    eid = state.get("engagement_id", engagement_id)
    decl = dict(state)
    decl["stage_a"] = (state.get("client_submission") or {}).get("stage_a") or {}
    decl.setdefault("annex_iii_sections", state.get("declared_annex_iii_sections", []))
    t17 = build_t17(eid, decl, now)
    t17_ref = {
        "uri": f"customer://{eid}/T17_compliance_matrix.json",
        "sha256": "",
        "template_id": "T17_compliance_matrix",
    }
    t18 = build_t18(eid, decl, t17_ref, now)
    return t17, t18, now


def print_summary(engagement_id: str, state: dict[str, Any], t17: dict[str, Any],
                  summary: dict[str, Any], customer_dir: Any) -> None:
    """Print the human-readable finalisation summary."""
    print(f"=== finalize {engagement_id} ===")
    print(f"resolved={summary['resolved']} unresolved={summary['unresolved']} "
          f"still_hitl={summary['still_hitl']}")
    print(f"report_status : {t17.get('report_status')}")
    print(f"final_verdict : {state.get('final_verdict')}")
    print(f"KPIs          : completeness={state.get('completeness_score')} "
          f"coverage={state.get('regulatory_coverage_pct')}")
    print("compliance_matrix:")
    for article, verdict in sorted(state.get("compliance_matrix", {}).items()):
        print(f"  {article:14s} {verdict}")
    print(f"\nwritten → {customer_dir}")
