"""Remediation-roadmap enrichment and radar-chart score extraction."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.roadmap_rules import (
    DOMAIN_TO_OWNER_FIELD,
    SEVERITY_MAP,
    deadline_weeks,
)
from aaa.platform.state.contacts import owner_for


def enrich_remediation_roadmap(
    items: list[dict[str, Any]],
    contacts: dict[str, Any],
    source_items: list[dict[str, Any]],
    control_domains: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Add owner, priority and deadline fields to CGSA remediation items.

    :param items: Ingested remediation-roadmap entries.
    :param contacts: Organisation contacts keyed by role field.
    :param source_items: Raw payload entries (fallback for missing fields).
    :param control_domains: ``{control_id: domain_id}`` from the CGSA domains
        tree; an explicit ``domain_id`` on the item or source row still wins.
    :returns: Enriched copies of *items*.
    """
    domains = control_domains or {}
    enriched: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        source = source_items[idx] if idx < len(source_items) else {}
        domain_id = (item.get("domain_id") or source.get("domain_id")
                     or domains.get(str(item.get("control_id"))) or "")
        owner_field = DOMAIN_TO_OWNER_FIELD.get(domain_id, "technical_lead")
        severity = str(item.get("gap_severity") or source.get("gap_severity") or "").lower()
        priority_label, fallback_weeks = SEVERITY_MAP.get(severity, ("long_term", 52))
        enriched_item = dict(item)
        enriched_item["domain_id"] = domain_id
        enriched_item["assigned_owner"] = owner_for(owner_field, contacts)
        enriched_item["priority_label"] = priority_label
        enriched_item["deadline_weeks"] = deadline_weeks(item, source, fallback_weeks)
        enriched.append(enriched_item)
    return enriched


def domain_scores_for_chart(payload: Any) -> dict[str, float]:
    """Extract ``{domain_label: score}`` from CGSA domains for the radar chart.

    :param payload: Raw CGSA payload dictionary.
    :returns: Mapping of domain label to numeric score.
    """
    if not isinstance(payload, dict):
        return {}
    domain_scores: dict[str, float] = {}
    for domain in payload.get("domains", []) or []:
        domain_id = domain.get("domain_id", "")
        label = f"{domain_id} {domain.get('domain_name', domain_id)}".strip()
        try:
            domain_scores[label] = float(domain.get("domain_score", 0.0))
        except (TypeError, ValueError):
            domain_scores[label] = 0.0
    return domain_scores
