"""T14's blocking findings, each carrying every article its control maps to.

The CGSA ingest records all of a control's articles as ``eu_ai_act_articles`` — many
controls name more than one — and the compliance matrix reads that list.
T14 kept only the singular ``eu_ai_act_article``, so the artefact the Verifier reviews
showed C02 filed under Art. 9 alone while its own text names Art. 5 too, and the
Verifier refused it as understating the obligations (T-20260914-056).
"""
from __future__ import annotations

from typing import Any


def _finding(f: dict[str, Any]) -> dict[str, Any]:
    """One blocking finding in T14's shape; the article list only when the finding has one."""
    row = {
        "control_id": f.get("control_id", ""),
        "control_name": f.get("control_name", ""),
        "finding": f.get("finding", ""),
        "eu_ai_act_article": f.get("eu_ai_act_article", ""),
        "remediation_action": f.get("remediation_action", ""),
        "gap_severity": f.get("gap_severity"),
    }
    articles = [str(a) for a in (f.get("eu_ai_act_articles") or []) if a]
    if articles:
        row["eu_ai_act_articles"] = articles
    return row


def blocking_findings_section(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise the CGSA blocking findings for T14.

    :param handoff: The CGSA ``aaa_phase5_handoff`` block.
    :returns: One row per blocking finding.
    """
    return [_finding(f) for f in (handoff.get("blocking_findings", []) or [])]


__all__ = ["blocking_findings_section"]
