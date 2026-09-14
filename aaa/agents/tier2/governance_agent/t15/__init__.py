"""T15 Monitoring & Logging Review artefact builder (Art. 12 / 17 / 72)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.t15.evidence import Found, evidence_sections
from aaa.agents.tier2.governance_agent.t15.graded import graded_articles
from aaa.agents.tier2.governance_agent.t15.questions import T15_QUESTIONS
from aaa.agents.tier2.governance_agent.t15.sections import cgsa_ops_xrefs
from aaa.tools.cgsa_ingest import IngestResult

_QUOTED = ("Evidence fields quote the provider's own documents: they record what is "
           "documented, not a test of the controls.")


def build_t15(
    engagement_id: str, t01b: dict[str, Any], result: IngestResult, now: str,
    found: Found | None = None, scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the T15 Monitoring & Logging Review from Annex IV §3/§9 and the documents.

    :param engagement_id: Engagement identifier.
    :param t01b: Annex IV dossier (Stage B intake).
    :param result: Validated CGSA ingest result (for D6 cross-references).
    :param now: ISO-8601 generation timestamp.
    :param found: Grounded answers to :data:`T15_QUESTIONS`; ``None`` when none were sought.
    :param scope: State-like ``{risk_tier, …}``; articles that do not bind it are NOT_APPLICABLE.
    :returns: T15 payload matching the template schema.
    """
    found = found or {}
    monitoring_text = (t01b.get("monitoring_measures") or "").strip()
    logging_text = (t01b.get("logging_capabilities") or "").strip()
    post_market_uri = t01b.get("post_market_plan_uri")

    articles, overall, graded = graded_articles(t01b, found, scope)
    observations = ([] if monitoring_text else ["No monitoring measures documented in Annex IV §3."])
    observations += graded
    observations += [_QUOTED] if any(found.values()) else []

    hitl = overall == "FAIL"
    return {
        "engagement_id": engagement_id,
        **evidence_sections(monitoring_text, logging_text, post_market_uri, found),
        **articles,
        "cgsa_cross_references": cgsa_ops_xrefs(result),
        "observations": observations,
        "overall_ops_verdict": overall,
        "hitl_required": hitl,
        "hitl_reason": ("Monitoring/logging evidence missing or non-compliant." if hitl else None),
        "generated_at": now,
    }


__all__ = ["T15_QUESTIONS", "build_t15"]
