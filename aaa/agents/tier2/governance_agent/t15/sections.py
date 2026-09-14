"""Section builders and verdict rules for the T15 artefact."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest import IngestResult


def verdict_from_qms(harmonised: list[str], monitoring: bool) -> str:
    """Art. 17 QMS verdict from standards coverage + monitoring evidence."""
    if harmonised and monitoring:
        return "PASS"
    if harmonised or monitoring:
        return "PASS_WITH_OBSERVATIONS"
    return "FAIL"


def overall_ops_verdict(statuses: list[str]) -> str:
    """Aggregate the three article statuses into the overall ops verdict."""
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS_WITH_OBSERVATIONS" in statuses:
        return "PASS_WITH_OBSERVATIONS"
    if all(s == "PASS" for s in statuses):
        return "PASS"
    return "PASS_WITH_OBSERVATIONS"


def cgsa_ops_xrefs(result: IngestResult) -> list[dict[str, Any]]:
    """Lift CGSA D6 (Monitoring & Incident Response) controls into T15 xrefs."""
    xrefs: list[dict[str, Any]] = []
    for dom in result.payload.get("domains", []) or []:
        if dom.get("domain_id") != "D6":
            continue
        for ctrl in dom.get("controls", []) or []:
            for article in ctrl.get("eu_ai_act_articles", []) or []:
                xrefs.append({
                    "article": article,
                    "control_id": ctrl.get("control_id", ""),
                    "rationale": ctrl.get("evidence_summary"),
                })
    return xrefs
