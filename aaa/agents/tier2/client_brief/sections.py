"""The per-article section and the summary table the brief renders."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.client_brief.blocks import _ARTICLE_BLOCKS
from aaa.agents.tier2.client_brief.constants import verdict_label
from aaa.agents.tier2.client_brief.lines import bullets, paragraph


def _matrix_table(state: dict[str, Any], sections: list[dict[str, Any]]) -> str:
    """Render the requirement-by-requirement summary table."""
    rows = "\n".join(
        f"| {s['article']} | {s['subject']} | {verdict_label(str(s['verdict']))} |"
        for s in sections)
    # Counted from the rows printed, not from the matrix: a heading that says
    # seventeen above a table of sixteen is the one error a reader cannot check.
    return (f"## The {len(sections)} requirements we assessed\n\n"
            "| Requirement | What it covers | Result |\n|---|---|---|\n" + rows + "\n")
def _article_section(index: int, section: dict[str, Any]) -> str:
    """Render one article's section, omitting the blocks it has nothing for."""
    parts = [f"### {index}. {section['subject']} — {section['article']} · "
             f"{verdict_label(str(section['verdict']))}\n"]
    if section.get("headline"):
        parts.append(f"**{paragraph(section['headline'])}**\n")
    for heading, key in _ARTICLE_BLOCKS:
        body = bullets(section.get(key)) if key != "why_this_verdict" \
            else paragraph(section.get(key))
        if body:
            parts.append(f"**{heading}**\n\n{body}\n")
    if not section.get("llm_written", True):
        parts.append("*This section was assembled directly from the audit's findings; "
                     "the narrative pass did not produce it.*\n")
    return "\n".join(parts)


__all__ = ["_article_section", "_matrix_table"]
