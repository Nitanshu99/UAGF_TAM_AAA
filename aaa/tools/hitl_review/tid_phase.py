"""Part 1 of the former ``hitl_review`` module (auto-split)."""
from __future__ import annotations

from datetime import datetime, timezone

_TID_PHASE: dict[str, str] = {
    "T02_system_card": "P1 Scope",
    "T03_annex_iii_mapping": "P1 Scope",
    "T04_risk_tier_decision": "P1 Scope",
    "T05_art43_decision": "P1 Scope",
    "T06_datasheet_for_datasets": "P2 Data Governance",
    "T07_data_quality_report": "P2 Data Governance",
    "T08_special_category_data_log": "P2 Data Governance",
    "T09_model_card": "P3 Model Validation",
    "T10_explainability_report": "P3 Model Validation",
    "T11_robustness_report": "P3 Model Validation",
    "T12_output_fairness_report": "P4 Output Fairness",
    "T13_output_sampling_log": "P4 Output Fairness",
    "T14_governance_findings": "P5 Governance",
    "T15_monitoring_logging_review": "P5 Governance",
    "T16_uagf_tam_l_evidence": "L-Branch",
}


#: `unverified` joins the escalations: the reviewer is the only remaining gate
#: on an artefact the Verifier never critiqued (P6). So does an unresolved
#: `rerun`: since fix 26 it holds its articles at INSUFFICIENT_EVIDENCE, and
#: `clear_unadmitted_insufficiency` can only release an artefact a human admits —
#: which it cannot do for one the packet never shows them (Q1).
_HITL_VERDICTS = {"escalate_hitl", "unverified", "rerun"}


DECISION_ACCEPT = "accept"               # admit the artefact as-is


DECISION_UPHOLD = "uphold_escalation"    # the escalation stands (finding remains)


DECISION_OVERRIDE = "override"           # set an explicit verdict on the artefact


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
