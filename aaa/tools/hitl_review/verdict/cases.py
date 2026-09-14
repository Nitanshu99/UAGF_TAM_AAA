"""Review cases derived from the audit verdict, not a Verifier escalation.

``hitl_cases`` enumerates only artefacts the Verifier escalated. But
``node_hitl_checkpoint`` independently sets ``hitl_required`` on a FAIL
verdict, so an engagement can end with "a human must review this" and no
cases at all — the reviewer is told to act and handed nothing. This module
derives the missing cases from the material findings that caused the verdict,
keyed to the artefact of the phase that raised each one so the packet schema
(and ``finalize_hitl``) is unchanged.
"""
from __future__ import annotations

from typing import Any

#: phase key (as findings record it) → the artefact a reviewer should open.
_PHASE_ARTEFACT: dict[str, str] = {
    "P1": "T02_system_card",
    "P2": "T07_data_quality_report",
    "P3": "T09_model_card",
    "P4": "T12_output_fairness_report",
    "P5": "T14_governance_findings",
    "L": "T16_uagf_tam_l_evidence",
}

#: findings at or above this materiality justify a human review case.
_REVIEWABLE = {"material", "possibly_material"}

#: State keys carrying findings. ``blocking_findings`` is what the pipeline
#: actually populates; ``findings`` is accepted for hand-built states.
_FINDING_KEYS = ("blocking_findings", "findings")

#: Findings record articles under ``eu_ai_act_articles``; older/hand-built
#: records use ``articles``.
_ARTICLE_KEYS = ("eu_ai_act_articles", "articles")


def finding_articles(finding: dict[str, Any]) -> list[str]:
    """Return a finding's cited articles under either field name.

    :param finding: A finding dict.
    :type finding: dict[str, Any]
    :returns: The cited EU AI Act articles.
    :rtype: list[str]
    """
    for key in _ARTICLE_KEYS:
        if finding.get(key):
            return list(finding[key])
    return []


def _phase_key(finding: dict[str, Any]) -> str:
    """Return the normalised phase key a finding came from.

    :param finding: A finding dict (carries ``source_phase``).
    :type finding: dict[str, Any]
    :returns: Key into :data:`_PHASE_ARTEFACT`, or ``""`` when unmappable.
    :rtype: str
    """
    raw = str(finding.get("source_phase") or "").strip().upper()
    return raw if raw in _PHASE_ARTEFACT else raw[:2] if raw[:2] in _PHASE_ARTEFACT else ""


def verdict_case_findings(state: dict) -> dict[str, list[dict[str, Any]]]:
    """Group reviewable findings by the artefact a human should examine.

    :param state: The provisional final AuditState.
    :type state: dict
    :returns: ``{template_id: [finding, …]}``; empty when nothing qualifies.
    :rtype: dict[str, list[dict[str, Any]]]
    """
    collected: list[dict[str, Any]] = []
    for key in _FINDING_KEYS:
        collected += list(state.get(key) or [])
    grouped: dict[str, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for finding in collected:
        fid = str(finding.get("finding_id") or id(finding))
        if fid in seen:
            continue
        seen.add(fid)
        if str(finding.get("materiality") or "").lower() not in _REVIEWABLE:
            continue
        tid = _PHASE_ARTEFACT.get(_phase_key(finding))
        if tid:
            grouped.setdefault(tid, []).append(finding)
    return grouped
