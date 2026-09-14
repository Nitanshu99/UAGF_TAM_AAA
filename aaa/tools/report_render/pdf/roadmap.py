"""The remediation roadmap and the management-response tables."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Spacer

from aaa.tools.report_render.numbers import shorten
from aaa.tools.report_render.pdf.elements import section
from aaa.tools.report_render.pdf.management import _management
from aaa.tools.report_render.pdf.theme import STYLES


def _roadmap(t18: dict[str, Any]) -> list[Any]:
    """Render the remediation roadmap: what to do, by when, and who owns it."""
    roadmap = [r for r in (t18.get("remediation_roadmap") or []) if r]
    if not roadmap:
        return []
    flow = section("Remediation roadmap",
                   "Steps required before the affected articles can be re-assessed.")
    for i, step in enumerate(roadmap, 1):
        if not isinstance(step, dict):
            flow.append(Paragraph(f"{i}. {step}", STYLES["body"]))
            continue
        ref = step.get("finding_id") or step.get("control_id") or ""
        due = step.get("deadline_weeks")
        meta = " · ".join(part for part in (
            str(step.get("priority_label") or "").replace("_", " ") or "",
            f"within {due} weeks" if due else "",
            f"owner: {step.get('assigned_owner')}" if step.get("assigned_owner") else "",
        ) if part)
        flow.append(Paragraph(
            f'{i}. <b>{ref}</b> {shorten(str(step.get("action") or step.get("recommended_action") or ""))}',
            STYLES["body"]))
        if meta:
            flow.append(Paragraph(meta, STYLES["muted"]))
    flow.append(Spacer(1, 6))
    return flow


__all__ = ["_management", "_roadmap"]
