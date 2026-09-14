"""Per-article compliance breakdown table for the customer-facing PDF."""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from aaa.tools.report_render.numbers import shorten
from aaa.tools.report_render.pdf.elements import section
from aaa.tools.report_render.pdf.matrix_row import _notes, _row
from aaa.tools.report_render.pdf.theme import BORDER, STYLES, SURFACE


def build_matrix(t17: dict[str, Any]) -> list[Any]:
    """Build the article breakdown section from the T17 payload.

    :param t17: The T17 compliance-matrix payload.
    :type t17: dict[str, Any]
    :returns: Section flowables (empty when no articles are present).
    :rtype: list[Any]
    """
    articles = t17.get("articles") or []
    if not articles:
        return []
    flow = section("Compliance matrix",
                   "EU AI Act article verdicts derived from admitted, verifier-accepted evidence.")
    notes: dict[str, int] = _notes(articles)
    seen: set[int] = set()
    header = [Paragraph(f"<b>{h}</b>", STYLES["muted"])
              for h in ("Article", "Verdict", "Findings", "Basis")]
    table = Table([header] + [_row(e, notes, seen) for e in articles],
                  colWidths=[3.2 * cm, 2.6 * cm, 1.8 * cm, 8.9 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [None, SURFACE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 6))
    for text, note in sorted(notes.items(), key=lambda kv: kv[1]):
        flow.append(Paragraph(f"<b>Note {note}.</b> {shorten(text)}", STYLES["muted"]))
    return flow
