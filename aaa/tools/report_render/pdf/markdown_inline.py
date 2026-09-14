"""Inline Markdown → ReportLab paragraph markup.

ReportLab's ``Paragraph`` accepts a small HTML subset, so the brief's inline
spans (``**bold**`` and `` `code` ``) map onto it directly. Everything else is
escaped first: the brief quotes customer-supplied strings — provider names,
column names, file paths — and an unescaped ``&`` or ``<`` in one of those
raises inside the PDF build, which would lose the whole document to a stray
character in a field the customer typed.
"""
from __future__ import annotations

import re

#: ``**bold**`` — non-greedy so two spans on one line stay separate.
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
#: `` `code` `` — rendered in a mono face rather than dropped.
_CODE = re.compile(r"`([^`]+)`")


def escape(text: str) -> str:
    """XML-escape *text* for a ReportLab paragraph.

    :param text: Raw Markdown text.
    :returns: The text with ``&``, ``<`` and ``>`` escaped.
    """
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def inline(text: str) -> str:
    """Convert one line of inline Markdown to ReportLab markup.

    :param text: A single Markdown line, without its block prefix.
    :returns: Paragraph markup with bold and code spans applied.
    """
    out = escape(text.strip())
    out = _BOLD.sub(r"<b>\1</b>", out)
    return _CODE.sub(r'<font face="Courier">\1</font>', out)


__all__ = ["escape", "inline"]
