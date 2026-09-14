"""A three-row CGSA remediation roadmap in the S5 dialect, with its domains tree.

Synthetic, so CI can run it; shaped like the real case-06 export (one critical, one
high with a 4-week timeline, one medium with none).
"""
from __future__ import annotations

ROWS = [
    {"rank": 1, "control_id": "C36", "control_name": "Incident Management",
     "gap_severity": "critical", "current_score": 0, "target_score": 3,
     "action": "Create a playbook.", "eu_ai_act_article": "Article 9",
     "effort_estimate": "high", "timeline_weeks": 6, "priority_rationale": "Score 0."},
    {"rank": 2, "control_id": "C07", "control_name": "Data Lineage", "gap_severity": "high",
     "current_score": 1, "target_score": 3, "action": "Record lineage.",
     "eu_ai_act_article": "Article 10", "effort_estimate": "medium", "timeline_weeks": 4,
     "priority_rationale": "Score 1."},
    {"rank": 3, "control_id": "C12", "control_name": "Logging", "gap_severity": "medium",
     "current_score": 2, "target_score": 3, "action": "Retain logs.",
     "eu_ai_act_article": "Article 12", "effort_estimate": "low", "timeline_weeks": None,
     "priority_rationale": "Score 2."},
]
PAYLOAD = {"remediation_roadmap": ROWS, "domains": [
    {"domain_id": "D2", "controls": [{"control_id": "C07"}]},
    {"domain_id": "D4", "controls": [{"control_id": "C12"}, {"control_id": "C36"}]}]}
