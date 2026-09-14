"""Part 1 of the former ``initial_state`` module (auto-split)."""
from __future__ import annotations

from typing import Any


def _empty_cgsa_state() -> dict[str, Any]:
    """Return the pristine §5.4 CGSA hand-off surface for a new engagement."""
    empty_lists = ("cgsa_blocking_findings", "cgsa_positive_findings",
                   "cgsa_low_confidence_controls", "cgsa_recommended_follow_up")
    none_fields = ("cgsa_payload", "cgsa_source", "cgsa_schema_version",
                   "cgsa_composite_maturity_score",
                   "cgsa_composite_maturity_label", "cgsa_domain_scores",
                   "cgsa_eu_ai_act_coverage_pct", "cgsa_csp_satisfiable",
                   "cgsa_governance_verdict", "cgsa_phase5_verdict", "cgsa_phase5_narrative",
                   "cgsa_report_url", "cgsa_risk_tier_match")
    state: dict[str, Any] = {key: None for key in none_fields}
    state.update({key: [] for key in empty_lists})
    return state
