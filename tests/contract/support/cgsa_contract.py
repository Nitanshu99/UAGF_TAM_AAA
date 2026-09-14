"""Shared fixture discovery and required-key list for the CGSA contract tests."""
from __future__ import annotations

import pathlib

_FIXTURE_DIR = (
    pathlib.Path(__file__).parents[3] / "scripts" / "fixtures" / "cgsa"
)

#: The §5.4 state_delta keys that every IngestResult must populate.
REQUIRED_STATE_KEYS = (
    "cgsa_payload", "cgsa_schema_version", "cgsa_composite_maturity_score",
    "cgsa_composite_maturity_label", "cgsa_eu_ai_act_coverage_pct",
    "cgsa_csp_satisfiable", "cgsa_governance_verdict", "cgsa_phase5_verdict",
    "cgsa_phase5_narrative", "cgsa_blocking_findings", "cgsa_positive_findings",
    "cgsa_low_confidence_controls", "cgsa_recommended_follow_up",
    "cgsa_risk_tier_match", "harmonised_standards_applied",
)


def fixture_paths() -> list[pathlib.Path]:
    """Collect all *.json files under the cgsa fixture directory."""
    return sorted(_FIXTURE_DIR.glob("*.json"))
