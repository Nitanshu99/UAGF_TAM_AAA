"""The management-response table the report closes its findings section with."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Spacer

from aaa.tools.report_render.numbers import shorten
from aaa.tools.report_render.pdf.elements import section
from aaa.tools.report_render.pdf.tables import kv_table
from aaa.tools.report_render.pdf.theme import STYLES


def _management(t18: dict[str, Any]) -> list[Any]:
    """Render the client-fill management-response block (Q17).

    The shell has always been built into T18 and has never been rendered, so the
    client was asked for responses in a JSON they do not open.
    """
    rows = [r for r in (t18.get("management_response") or []) if r]
    if not rows:
        return []
    flow = section("Management response",
                   "To be completed by the provider and returned to the audit team.")
    for row in rows:
        flow.append(Paragraph(
            f'<b>{row.get("finding_id", "")}</b>  '
            f'<font size="8">{row.get("materiality", "")}</font>', STYLES["body"]))
        flow.append(kv_table([
            ("Auditor recommendation", shorten(str(row.get("auditor_recommendation") or "—"))),
            ("Management response", str(row.get("management_response") or "—")),
            ("Action plan", str(row.get("action_plan") or "—")),
            ("Target completion", str(row.get("target_completion_date") or "—")),
            ("Responsible owner", str(row.get("responsible_owner") or "—")),
        ]))
        flow.append(Spacer(1, 6))
    return flow


__all__ = ["_management"]
