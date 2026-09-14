"""Internal-consistency reconciliation of the CGSA self-assessment."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.below import _below, below_own_threshold
from aaa.tools.findings import make_finding


def reconcile_cgsa(payload: Any) -> list[dict[str, Any]]:
    """Reconcile the CGSA self-assessment's internal consistency.

    A real auditor does not accept a maturity scorecard at face value: the
    headline control counts must match the detailed control list, and every
    below-threshold control must actually be identified.

    :param payload: Raw CGSA payload dictionary.
    :returns: Findings for each detected inconsistency (may be empty).
    """
    if not isinstance(payload, dict):
        return []
    findings: list[dict[str, Any]] = []
    scores = payload.get("overall_scores", {}) or {}
    domains = payload.get("domains", []) or []
    detailed = [c for d in domains for c in (d.get("controls", []) or [])]
    assessed = scores.get("controls_assessed")
    below = scores.get("controls_below_threshold")

    # A payload may legitimately ship a documented *subset* of controls; when it
    # says so explicitly, the count gap is an observation, not a material gap.
    partial = bool(scores.get("breakdown_is_partial") or payload.get("breakdown_is_partial"))
    count_severity = "observation" if partial else "possibly_material"

    if isinstance(assessed, int) and assessed != len(detailed):
        findings.append(make_finding(
            finding_id="P5-CGSA-COUNT",
            description=(
                f"CGSA self-assessment reports {assessed} controls assessed but only "
                f"{len(detailed)} are detailed in the domain breakdown; the remaining "
                f"{assessed - len(detailed)} are unverifiable."
            ),
            materiality=count_severity,
            articles=["Art.17"],
            source_phase="P5",
            recommendation="Provide the full per-control evidence behind the headline counts.",
            declared=assessed,
            observed=len(detailed),
        ))

    identified_below = [c for c in detailed if _below(c) or below_own_threshold(c)]
    if isinstance(below, int) and below > 0 and len(identified_below) < below:
        findings.append(make_finding(
            finding_id="P5-CGSA-BELOW",
            description=(
                f"CGSA reports {below} control(s) below threshold but the detailed "
                f"breakdown identifies only {len(identified_below)}; the unidentified "
                "below-threshold control(s) cannot be assessed."
            ),
            materiality=count_severity,
            articles=["Art.17"],
            source_phase="P5",
            recommendation="Name each below-threshold control and its remediation plan.",
            declared=below,
            observed=len(identified_below),
        ))
    return findings
