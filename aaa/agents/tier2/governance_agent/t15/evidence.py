"""Evidence blocks (monitoring / logging / post-market) for T15.

Every one of these fields was a hardcoded ``None`` or ``[]`` while the provider's
monitoring plan and technical documentation answered them (T-20260913-032). A flag
is ``True`` only where a document passage says so, ``False`` only where one says
the opposite, a text field quotes its passage, and anything no passage answers stays
``None`` — unknown, not absent.
"""
from __future__ import annotations

from typing import Any, Mapping

from aaa.agents.tier2.governance_agent.t15.tools import TOOL_NAMES
from aaa.tools.document_evidence import Evidence

Found = Mapping[str, Evidence | None]


def _cite(found: Found, key: str) -> str | None:
    evidence = found.get(key)
    return evidence.cite() if evidence else None


def tool_evidence(found: Found, key: str) -> Evidence | None:
    """Evidence that tool *key* exists — operating evidence, where monitoring is declared unbuilt."""
    return found.get(f"{key}_operating") if found.get("monitoring_gap") else (
        found.get(f"{key}_operating") or found.get(key))


def monitoring_tools(found: Found) -> list[str]:
    """The monitoring mechanisms the documents evidence, each with its source."""
    return [f"{name} ({evidence.origin})" for key, name in TOOL_NAMES.items()
            if (evidence := tool_evidence(found, key))]


def _tool_flag(found: Found, key: str) -> bool | None:
    if tool_evidence(found, key):
        return True
    return False if found.get(f"{key}_absent") else None


def evidence_refs(found: Found, *keys: str) -> list[str]:
    """Where the grounded answers to *keys* came from, without repeats."""
    uris = (evidence.source_uri for key in keys if (evidence := found.get(key)))
    return list(dict.fromkeys(uris))


def evidence_sections(monitoring_text: str, logging_text: str, post_market_uri: Any,
                      found: Found) -> dict[str, dict[str, Any]]:
    """Build the monitoring / logging / post-market evidence blocks."""
    return {
        "monitoring_evidence": {
            "monitoring_measures_documented": bool(monitoring_text),
            "monitoring_summary": monitoring_text or None,
            "monitoring_tools": monitoring_tools(found),
            "drift_detection_documented": _tool_flag(found, "drift"),
            "performance_dashboards_documented": _tool_flag(found, "dashboards"),
        },
        "logging_evidence": {
            "logging_capabilities_documented": bool(logging_text),
            "logging_summary": logging_text or None,
            "automatic_logging_enabled": True if found.get("automatic_logging") else None,
            "log_retention_period": _cite(found, "log_retention"),
            "log_integrity_controls": _cite(found, "log_integrity"),
        },
        "post_market_monitoring": {
            "plan_provided": bool(post_market_uri),
            "plan_uri": post_market_uri,
            "incident_reporting_documented": True if found.get("incident_reporting") else None,
            "serious_incident_threshold_defined": True if found.get("incident_threshold") else None,
        },
    }


__all__ = ["Found", "evidence_refs", "evidence_sections", "monitoring_tools", "tool_evidence"]
