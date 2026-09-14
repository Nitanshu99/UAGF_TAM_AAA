"""Client-fill management-response shell for the T18 report."""
from __future__ import annotations

from typing import Any


def management_response_shell(
    findings: list[dict[str, Any]],
    remediation: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Generate client-fill management-response rows for material findings.

    :param findings: Blocking + positive findings from the engagement.
    :param remediation: Remediation-roadmap items keyed by ``control_id``.
    :returns: One pre-filled response row per material / possibly-material
        finding, with management fields left as placeholders.
    """
    by_control = {str(item.get("control_id", "")): item for item in remediation}
    shell: list[dict[str, str]] = []
    for idx, finding in enumerate(findings, start=1):
        materiality = finding.get("materiality")
        if materiality not in {"material", "possibly_material"}:
            continue
        remediation_item = by_control.get(str(finding.get("control_id", "")), {})
        recommendation = (finding.get("recommendation")
                          or finding.get("recommended_action")
                          or remediation_item.get("recommended_action")
                          or remediation_item.get("gap_detail")
                          or finding.get("gap_detail")
                          or "")
        owner = (finding.get("assigned_owner")
                 or remediation_item.get("assigned_owner")
                 or "[To be assigned]")
        shell.append({
            "finding_id": str(finding.get("finding_id") or f"F-{idx:03d}"),
            "finding_summary": str(finding.get("description", ""))[:200],
            "materiality": str(materiality),
            "auditor_recommendation": str(recommendation),
            "management_response": "[Management response pending]",
            "action_plan": "[Action plan pending]",
            "target_completion_date": "[Date pending]",
            "responsible_owner": str(owner),
        })
    return shell
