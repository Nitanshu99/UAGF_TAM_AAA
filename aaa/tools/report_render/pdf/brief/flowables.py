"""Line-by-line conversion of the client-brief Markdown into ReportLab flowables.

Only the constructs the brief actually emits are handled — ATX headings,
blockquote, ``-`` bullets, pipe tables, and the ``**bold**`` / `` `code` ``
inline spans. Anything else falls through to a paragraph rather than being
dropped, which keeps an unrecognised line visible to the reader instead of
silently missing from their copy.
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, Paragraph, Spacer

from aaa.tools.report_render.pdf.brief.blocks import consume_table, is_table_row
from aaa.tools.report_render.pdf.markdown_inline import inline
from aaa.tools.report_render.pdf.theme import STYLES

_BULLET = ParagraphStyle("brief_bullet", parent=STYLES["body"],
                         leftIndent=12, bulletIndent=2, spaceAfter=3)
_HEADINGS = {1: "title", 2: "h1", 3: "h2", 4: "h2"}


def _heading(line: str) -> list[Any]:
    """Build the flowables for an ATX heading line.

    :param line: The raw Markdown line, leading ``#`` marks included.
    :returns: Spacer + heading paragraph (+ trailing spacer for the title).
    """
    depth = len(line) - len(line.lstrip("#"))
    style = STYLES[_HEADINGS.get(depth, "h2")]
    flow: list[Any] = [Spacer(1, 8 if depth > 1 else 2),
                       Paragraph(inline(line.lstrip("#")), style)]
    if depth == 1:
        flow.append(Spacer(1, 6))
    return flow


def _line_flowables(line: str) -> list[Any]:
    """Build the flowables for one non-table, non-blank line.

    :param line: The raw Markdown line.
    :returns: The flowables that render it.
    """
    if line.startswith("#"):
        return _heading(line)
    if line.startswith(">"):
        return [Spacer(1, 4),
                KeepTogether(Paragraph(inline(line.lstrip("> ")), STYLES["h2"])),
                Spacer(1, 4)]
    if line.lstrip().startswith("- "):
        return [Paragraph(inline(line.lstrip()[2:]), _BULLET, bulletText="•")]
    return [Paragraph(inline(line), STYLES["body"]), Spacer(1, 4)]


def markdown_flowables(markdown: str) -> list[Any]:
    """Convert the brief's Markdown into ReportLab flowables.

    :param markdown: The client brief as written by the ClientBrief agent.
    :returns: Flowables in document order.
    """
    lines = markdown.splitlines()
    flow: list[Any] = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if not line.strip():
            index += 1
            continue
        if is_table_row(line):
            table, index = consume_table(lines, index)
            flow.extend([Spacer(1, 6), table, Spacer(1, 8)])
            continue
        flow.extend(_line_flowables(line))
        index += 1
    return flow


__all__ = ["markdown_flowables"]
