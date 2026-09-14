"""Management-response section and full text-body assembly."""
from __future__ import annotations

from typing import Any

from aaa.tools.report_render.text.header import header_lines, opinion_lines, summary_kpi_lines
from aaa.tools.report_render.text.sections import (
    art43_matrix_lines,
    artefact_lines,
    findings_roadmap_lines,
)

_MANAGEMENT_INTRO = (
    "The following table presents the audit findings requiring management attention, "
    "together with placeholder fields for management responses. The client organisation "
    "is requested to complete the 'Management Response', 'Action Plan', 'Target "
    "Completion Date', and 'Responsible Owner' columns and return the completed table "
    "to the audit team within 10 business days of receiving this draft report."
)


def management_lines(t18: dict[str, Any]) -> list[str]:
    """Render the management-response table (may be empty)."""
    management = t18.get("management_response", []) or []
    if not management:
        return []
    lines = [
        "9. Management Response", "-" * 70, _MANAGEMENT_INTRO, "",
        "Finding ID | Finding | Materiality | Recommendation | Management Response | "
        "Action Plan | Target Date | Owner",
    ]
    for row in management:
        lines.append(
            f"{row.get('finding_id', '')} | {row.get('finding_summary', '')} | "
            f"{row.get('materiality', '')} | {row.get('auditor_recommendation', '')} | "
            f"{row.get('management_response', '')} | {row.get('action_plan', '')} | "
            f"{row.get('target_completion_date', '')} | {row.get('responsible_owner', '')}")
    lines.append("")
    return lines


def _build_text_body(t18: dict[str, Any]) -> str:
    """Plain-text rendering used when reportlab is unavailable.

    :param t18: The T18 audit-report payload.
    :returns: The complete report body as one newline-joined string.
    """
    lines = (header_lines(t18) + opinion_lines(t18) + summary_kpi_lines(t18)
             + art43_matrix_lines(t18) + artefact_lines(t18) + findings_roadmap_lines(t18)
             + management_lines(t18))
    cgsa_url = t18.get("cgsa_report_url")
    if cgsa_url:
        lines += [f"Full CGSA governance report: {cgsa_url}", ""]
    lines += ["-" * 70, f"Generated at : {t18.get('generated_at', '')}", "End of report."]
    return "\n".join(lines)
