"""What we checked, grouped by outcome and named in the reader's language.

The same page used to print ``Art.10§2(f)`` against ``INSUFFICIENT_EVIDENCE``
in a monospace table. Both halves of that row are correct and neither is
readable, so each article is now headed by its subject — "Checking datasets for
bias" — taken from the vocabulary the client brief already writes in, with the
article reference kept underneath for anyone who needs to cite it.
"""
from __future__ import annotations

import html

import streamlit as st

from aaa.agents.tier2.client_brief.constants import article_title
from aaa.ui.styles import section_title, verdict_pill
from aaa.ui.wizard.step4.header import article_parts

#: Verdict → (group heading, sort rank). Worst first: the reader's first
#: question is what is broken.
_GROUPS: dict[str, tuple[str, int]] = {
    "FAIL": ("Not met", 0),
    "INSUFFICIENT_EVIDENCE": ("Could not be checked", 1),
    "PASS_WITH_OBSERVATIONS": ("Met, with observations", 2),
    "PASS": ("Met", 3),
}
_OTHER = ("Does not apply to your system", 4)


def _group(verdict: str) -> tuple[str, int]:
    """Heading and rank for a matrix *verdict*."""
    return _GROUPS.get(verdict.upper(), _OTHER)


def _row(article: str, verdict: str, index: int, parts: list[tuple[str, str]]) -> str:
    """One article row: subject, reference, outcome, and the paragraphs refining it.

    Case 05 listed Art.10 as "Not met" and Art.10§2(f) as "Could not be checked" in
    another group, counted twice against a tile that counts articles (T-20260913-104).
    """
    inner = "".join(
        f'<div class="aaa-article-part"><div><span class="subject">'
        f"{html.escape(article_title(ref))}</span> "
        f'<span class="ref">{html.escape(ref)}</span></div>'
        f"<div>{verdict_pill(v)}</div></div>" for ref, v in parts)
    return (f'<div class="aaa-article-row" style="--i:{min(index, 8)}">'
            f'<div><div class="subject">{html.escape(article_title(article))}</div>'
            f'<div class="ref">{html.escape(article)}</div></div>'
            f"<div>{verdict_pill(verdict)}</div>"
            f'{f"<div class=parts>{inner}</div>" if inner else ""}</div>')


def grouped_rows(matrix: dict) -> list[tuple[str, list[str]]]:
    """``(heading, row markups)`` per outcome group, worst first, counted over articles.

    :param matrix: Article → verdict mapping.
    """
    buckets: dict[str, list[tuple[str, str, list[tuple[str, str]]]]] = {}
    for article, (verdict, parts) in article_parts(matrix).items():
        buckets.setdefault(_group(verdict)[0], []).append((article, verdict, parts))
    order = sorted(buckets, key=lambda h: min(_group(v)[1] for _, v, _p in buckets[h]))
    return [(h, [_row(a, v, i, p) for i, (a, v, p) in enumerate(sorted(buckets[h]))])
            for h in order]


def render_articles(final: dict) -> None:
    """Render the article breakdown, grouped worst-outcome first.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    matrix: dict = final.get("compliance_matrix") or {}
    if not matrix:
        return
    section_title("What we checked",
                  "Every EU AI Act obligation that applies to your system, and "
                  "how yours stands against it.")
    for heading, rows in grouped_rows(matrix):
        expanded = heading in ("Not met", "Could not be checked")
        with st.expander(f"{heading}  ·  {len(rows)}", expanded=expanded):
            st.markdown("".join(rows), unsafe_allow_html=True)
