"""Per-article status blocks for the T15 artefact.

Art. 12 and Art. 72 carry the nonconformity grades from :mod:`.grading`, whose
rationales name every essential element and quote the passages behind them; Art. 17
keeps the harmonised-standard rule and names the standard the provider references.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.t15.evidence import Found, evidence_refs
from aaa.agents.tier2.governance_agent.t15.grading import Grade
from aaa.agents.tier2.governance_agent.t15.qms import qms_rationale, qms_reference

_ELEMENT_KEYS = ("accuracy_operating", "accuracy_absent", "drift_operating", "drift_absent",
                 "fairness_operating", "fairness_absent", "field_data_operating",
                 "field_data_absent", "incident_reporting", "monitoring_gap")


def article_sections(grades: tuple[Grade, str, Grade], harmonised: list[str],
                     post_market_uri: Any, found: Found,
                     other: list[str] | None = None) -> dict[str, Any]:
    """Build the Art. 12 / 17 / 72 status blocks of T15.

    :param grades: The Art. 12 grade, the Art. 17 status and the Art. 72 grade.
    :param other: Declared non-harmonised standards (``other_standards``).
    """
    art12, art17, art72 = grades
    return {
        "art12_record_keeping": {
            "status": art12.status,
            "rationale": art12.rationale,
            "evidence_refs": evidence_refs(found, "automatic_logging", "log_retention",
                                           "log_integrity", "logging_gap"),
        },
        "art17_qms": {
            "status": art17,
            "rationale": qms_rationale(art17, harmonised, other),
            "qms_standard_referenced": qms_reference(harmonised, other),
            "evidence_refs": evidence_refs(found, "qms"),
        },
        "art72_post_market_plan": {
            "status": art72.status,
            "rationale": art72.rationale,
            "evidence_refs": ([post_market_uri] if post_market_uri else [])
            + evidence_refs(found, *_ELEMENT_KEYS),
        },
    }


__all__ = ["article_sections"]
