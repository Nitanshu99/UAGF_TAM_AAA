"""Assemble the brief. Every verdict, count and article here comes from state.

The model writes the explanations; it does not get to state the result. Where a
number or a verdict appears in this document it was read out of the audit state,
so no reply can move a FAIL to a PASS by describing it warmly.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.client_brief.blocks import _FOOTER, _OVERVIEW_BLOCKS, _header
from aaa.agents.tier2.client_brief.lines import bullets, paragraph
from aaa.agents.tier2.client_brief.sections import _article_section, _matrix_table


def render_brief(state: dict[str, Any], engagement_id: str,
                 sections: list[dict[str, Any]], overview: dict[str, Any]) -> str:
    """Assemble the full client brief as Markdown.

    :param state: Final ``AuditState`` — the source of every verdict and count.
    :param engagement_id: Engagement identifier.
    :param sections: Per-article sections, worst verdict first.
    :param overview: The opening pass from :mod:`.synthesis`.
    :returns: The complete Markdown document.
    """
    parts = [_header(state, engagement_id)]
    for heading, key in _OVERVIEW_BLOCKS:
        body = paragraph(overview.get(key)) if key == "overall_explanation" \
            else bullets(overview.get(key))
        if body:
            parts.append(f"## {heading}\n\n{body}\n")
    parts.append(_matrix_table(state, sections))
    parts.append("## Requirement by requirement\n")
    parts.extend(_article_section(i, s) for i, s in enumerate(sections, start=1))
    parts.append(_FOOTER)
    return "\n".join(parts)
