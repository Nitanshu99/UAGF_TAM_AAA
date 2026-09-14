"""Article breakdown table for the results page (verdict + finding counts)."""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui import styles
from aaa.ui.styles.badges import verdict_badge


def _finding_counts(final: dict) -> dict[str, int]:
    """Count blocking findings per referenced EU AI Act article."""
    counts: dict[str, int] = {}
    for finding in final.get("blocking_findings") or []:
        for article in finding.get("eu_ai_act_articles") or finding.get("articles") or []:
            root = str(article).split("§", maxsplit=1)[0]
            counts[root] = counts.get(root, 0) + 1
    return counts


def render_matrix(final: dict) -> None:
    """Render the per-article breakdown from the compliance matrix.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    matrix: dict = final.get("compliance_matrix") or {}
    if not matrix:
        return
    styles.section_title(
        "Article breakdown",
        "EU AI Act article verdicts derived from admitted, verifier-accepted evidence.")
    counts = _finding_counts(final)
    rows = "".join(
        f"<tr><td><code>{html.escape(str(article))}</code></td>"
        f"<td>{verdict_badge(str(verdict))}</td>"
        f"<td>{counts.get(str(article).split('§', maxsplit=1)[0], 0) or '—'}</td></tr>"
        for article, verdict in sorted(matrix.items()))
    st.markdown(
        '<div class="aaa-card aaa-scroll-x"><table class="aaa-matrix">'
        "<thead><tr><th>EU AI Act article</th><th>Verdict</th><th>Findings</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)
