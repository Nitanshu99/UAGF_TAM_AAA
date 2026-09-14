"""Severity-grouped findings, positive findings, and the remediation roadmap."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Spacer

from aaa.tools.report_render.numbers import shorten
from aaa.tools.report_render.pdf.elements import section
from aaa.tools.report_render.pdf.roadmap import _management, _roadmap
from aaa.tools.report_render.pdf.theme import GREEN, SEVERITY_COLORS, SEVERITY_ORDER, STYLES

_SEVERITY_LABELS = {"material": "Material findings",
                    "possibly_material": "Possibly material findings",
                    "observation": "Observations"}


def _finding(item: dict[str, Any]) -> list[Any]:
    """Render one finding: coloured id line, description, recommendation."""
    color = SEVERITY_COLORS.get(item.get("materiality") or "", GREEN)
    articles = ", ".join(item.get("eu_ai_act_articles") or item.get("articles") or [])
    flow: list[Any] = [Paragraph(
        f'<font color="{color.hexval()}"><b>{item.get("finding_id", "")}</b></font>'
        f'  <font size="8">{articles}</font>', STYLES["body"])]
    flow.append(Paragraph(shorten(item.get("description") or ""), STYLES["cell"]))
    if item.get("recommendation"):
        flow.append(Paragraph(f"<b>Recommendation:</b> {item['recommendation']}",
                              STYLES["muted"]))
    flow.append(Spacer(1, 6))
    return flow


def build_findings(t18: dict[str, Any]) -> list[Any]:
    """Build the findings sections (blocking by severity, then positives).

    :param t18: The T18 audit-report payload.
    :type t18: dict[str, Any]
    :returns: Section flowables.
    :rtype: list[Any]
    """
    blocking = t18.get("blocking_findings") or []
    flow: list[Any] = []
    if blocking:
        flow += section(f"Findings ({len(blocking)})",
                        "Issues raised during the audit, ordered by materiality.")
        for severity in SEVERITY_ORDER:
            group = [f for f in blocking if f.get("materiality") == severity]
            if group:
                flow.append(Paragraph(f"{_SEVERITY_LABELS[severity]} ({len(group)})",
                                      STYLES["h2"]))
                for item in group:
                    flow += _finding(item)
    positives = t18.get("positive_findings") or []
    if positives:
        flow += section(f"Positive findings ({len(positives)})")
        for item in positives:
            flow.append(Paragraph(
                f'<font color="{GREEN.hexval()}"><b>{item.get("finding_id", "✓")}</b></font> '
                f'{item.get("description", "")}', STYLES["cell"]))
    flow += _roadmap(t18)
    flow += _management(t18)
    return flow
