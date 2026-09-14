"""A finding against articles that do not bind the engagement is an observation.

The compliance matrix already keeps only binding articles, so such a finding can
never carry a verdict; left ``material`` it still read as a non-conformity in the
findings register. A minimal-risk system's voluntary Phase 3/4 examination
(Art. 95; user decision T-20260913-075) is the case that makes this common.
"""
from __future__ import annotations

from aaa.tools.findings import articles_for
from aaa.tools.regulatory_coverage.engagement_scope import is_in_scope, scope_is_known


def restate_out_of_scope_findings(state: dict) -> None:
    """Downgrade, in place, each finding whose every article is outside the engagement's scope.

    :param state: The AuditState dict; ``blocking_findings`` entries are updated.
    """
    if not scope_is_known(state):
        return
    tier = state.get("risk_tier") or state.get("declared_risk_tier")
    for finding in state.get("blocking_findings") or []:
        articles = articles_for(finding)
        if (not articles or finding.get("materiality") not in {"material", "possibly_material"}
                or any(is_in_scope(state, a) for a in articles)):
            continue
        finding["materiality"] = "observation"
        finding["description"] = (
            f"{str(finding.get('description') or '').rstrip()} Recorded as an observation: "
            f"{', '.join(articles)} {'does' if len(articles) == 1 else 'do'} not bind this "
            f"'{tier}' engagement.").strip()
