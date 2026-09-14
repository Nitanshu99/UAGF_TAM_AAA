"""The key/value table and the verdict badge the report is built from."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle

from aaa.tools.report_render.pdf.theme import BORDER, STYLES, SURFACE


def badge(text: str, color: colors.Color) -> Table:
    """Build a colour-filled one-cell badge.

    :param text: Badge label.
    :type text: str
    :param color: Fill colour.
    :type color: colors.Color
    :returns: A single-cell table styled as a badge.
    :rtype: Table
    """
    cell = Table([[Paragraph(text, STYLES["banner"])]], hAlign="LEFT")
    cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return cell
def kv_table(rows: list[tuple[str, str]], col_widths: tuple[float, float] = (4.5, 11.5)) -> Table:
    """Build a two-column key/value table in the card style.

    :param rows: ``(label, value)`` pairs.
    :type rows: list[tuple[str, str]]
    :param col_widths: Column widths in centimetres.
    :type col_widths: tuple[float, float]
    :returns: The styled table.
    :rtype: Table
    """
    data = [[Paragraph(k, STYLES["muted"]), Paragraph(v, STYLES["cell"])] for k, v in rows]
    table = Table(data, colWidths=[col_widths[0] * cm, col_widths[1] * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


__all__ = ["badge", "kv_table"]
