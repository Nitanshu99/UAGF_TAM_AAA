"""Styling of the client brief's pipe table as a ReportLab ``Table``."""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle

from aaa.tools.report_render.pdf.markdown_inline import inline
from aaa.tools.report_render.pdf.theme import BORDER, INK, STYLES, SURFACE, verdict_color

#: Plain-language result → the verdict whose colour it borrows.
_RESULT_COLORS = {"met": "PASS", "not met": "FAIL",
                  "could not be checked": "DISCLAIMER_OF_OPINION"}


def _widths(columns: int) -> list[float]:
    """Column widths for a table of *columns* columns, filling the frame.

    :param columns: Number of columns in the table.
    :returns: One width per column, in points.
    """
    frame = 17.7 * cm
    if columns == 3:
        return [3.2 * cm, frame - 3.2 * cm - 3.4 * cm, 3.4 * cm]
    return [frame / columns] * columns


def styled_table(rows: list[list[str]]) -> Table:
    """Build the styled table for the collected *rows*.

    The last column of the brief's one table is a plain-language result, so it
    is coloured the way the same verdict is coloured everywhere else rather
    than left as undifferentiated text.

    :param rows: Header row first, then the body rows, as cell texts.
    :returns: The styled table.
    """
    header, body = rows[0], rows[1:]
    data: list[list[Any]] = [[Paragraph(f"<b>{inline(c)}</b>", STYLES["cell"])
                              for c in header]]
    for row in body:
        data.append([Paragraph(inline(c), STYLES["cell"]) for c in row])
    table = Table(data, colWidths=_widths(len(header)), repeatRows=1, hAlign="LEFT")
    style = [("BACKGROUND", (0, 0), (-1, 0), SURFACE),
             ("TEXTCOLOR", (0, 0), (-1, 0), INK),
             ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 5),
             ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 4),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for index, row in enumerate(body, start=1):
        mapped = _RESULT_COLORS.get(row[-1].strip().lower())
        if mapped:
            style.append(("TEXTCOLOR", (len(row) - 1, index),
                          (len(row) - 1, index), verdict_color(mapped)))
    table.setStyle(TableStyle(style))
    return table


__all__ = ["styled_table"]
