"""Pipe-table parsing for the client-brief Markdown renderer."""
from __future__ import annotations

from reportlab.platypus import Table

from aaa.tools.report_render.pdf.brief.table import styled_table


def is_table_row(line: str) -> bool:
    """Whether *line* opens or continues a Markdown pipe table.

    :param line: One Markdown line.
    :returns: ``True`` when the line starts with ``|``.
    """
    return line.lstrip().startswith("|")


def _cells(line: str) -> list[str]:
    """Split one pipe-table row into its cell texts.

    :param line: One pipe-table row.
    :returns: The stripped cell texts.
    """
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_rule(line: str) -> bool:
    """Whether *line* is the ``|---|---|`` header rule.

    :param line: One pipe-table row.
    :returns: ``True`` for the rule separating header from body.
    """
    return all(set(c) <= {"-", ":"} and c for c in _cells(line))


def consume_table(lines: list[str], start: int) -> tuple[Table, int]:
    """Collect the table beginning at *start* and build it.

    :param lines: All Markdown lines.
    :param start: Index of the first table row.
    :returns: The built table and the index of the first line after it.
    """
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and is_table_row(lines[index].rstrip()):
        line = lines[index].rstrip()
        if not _is_rule(line):
            rows.append(_cells(line))
        index += 1
    return styled_table(rows), index


__all__ = ["consume_table", "is_table_row"]
