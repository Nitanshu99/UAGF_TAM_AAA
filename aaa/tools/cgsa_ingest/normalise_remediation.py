"""Part 5 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.aggregate_low_confidence import _aggregate_low_confidence  # noqa: F401
from aaa.tools.cgsa_ingest.logger import (  # noqa: F401
    _LOW_CONFIDENCE_THRESHOLD,
    _REQUIRED_TOP_LEVEL_KEYS,
    _VENDORED_SCHEMA,
    CGSAIngestError,
    IngestResult,
    logger,
)
from aaa.tools.cgsa_ingest.schema_validate import schema_validate  # noqa: F401
from aaa.tools.cgsa_ingest.shallow_required_check import _shallow_required_check  # noqa: F401

#: Roadmap fields copied into state as the CGSA wrote them. They were dropped here,
#: so T14 printed an empty ``control_name`` on every row and enrichment could not
#: see the source's own ``timeline_weeks`` (T-20260913-006).
_VERBATIM_FIELDS = ("control_name", "eu_ai_act_article", "current_score",
                    "target_score", "effort_estimate", "timeline_weeks")


def _normalise_remediation(remediation: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise the raw remediation roadmap into the typed AuditState shape.

    The derived keys consumers already read are kept; the source's own fields are
    carried beside them unchanged, and only where the source has them.
    """
    return [
        {
            "rank": int(item.get("rank", idx + 1)),
            "control_id": item.get("control_id", ""),
            "gap_detail": item.get("priority_rationale") or item.get("action", ""),
            "gap_severity": item.get("gap_severity", "medium"),
            "recommended_action": item.get("action", ""),
            "target_date": None,
            **{key: item[key] for key in _VERBATIM_FIELDS if key in item},
        }
        for idx, item in enumerate(remediation)
    ]


def _infer_harmonised_standards(domains: list[dict[str, Any]]) -> bool:
    """
    Infer ``harmonised_standards_applied`` from CGSA controls.

    True when at least one control under domain D3 (Model Development and
    Testing) cites a recognised harmonised standard family in its
    ``source_frameworks`` array (e.g. ISO 42001).

    ``False`` carries two different facts, and only one of them is a finding
    (M10). The mock fixtures populate ``source_frameworks``; the **real S5
    export does not have the field at all** — its control schema is
    ``control_id, control_name, maturity_score, …, gap_detail``, with no
    framework information anywhere in the payload. Against that dialect this
    returned ``False`` for every engagement, silently, and the caller could not
    tell a measured negative from an unanswerable question. The default stays
    ``False`` — for an Annex III point 1 system that routes to Annex VII
    notified-body review, which is the more stringent of the two Art. 43 §1
    procedures and so the safe way to be wrong — but the unanswerable case now
    says so in the trail.

    :param domains: CGSA domain records, each holding ``controls``.
    :returns: True only where a D3 control positively cites a harmonised
        standard family.
    """
    harmonised = {"ISO 42001"}
    dialect_answers = False
    for dom in domains or []:
        for ctrl in dom.get("controls", []) or []:
            frameworks = ctrl.get("source_frameworks") or []
            if not frameworks:
                continue
            dialect_answers = True
            if dom.get("domain_id") == "D3" and any(fw in harmonised for fw in frameworks):
                return True
    if not dialect_answers:
        logger.warning(
            "CGSA payload carries no `source_frameworks` on any control, so "
            "harmonised_standards_applied could not be determined and defaults "
            "to False. This is the conservative default, not a finding that the "
            "provider applied no harmonised standard.")
    return False
