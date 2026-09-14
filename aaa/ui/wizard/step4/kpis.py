"""The four dashboard statistics, counted from the compliance matrix.

Counted over **articles**, not matrix rows. The matrix also carries paragraph
rows — ``Art.10§2(f)``, ``Art.15§1`` — that refine an article's verdict (fix 43)
and would otherwise be counted as requirements in their own right: the Mariposa
run read "4 of 17 requirements met" over a 15-article scope, with Art. 10 and
Art. 15 counted twice and "2 could not be checked" describing paragraphs of two
articles that had already been counted as not met.
"""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.step4.header import NOT_SCORED, article_rows
from aaa.ui.wizard.step4.tiles import kpi_tiles


def matrix_counts(matrix: dict) -> dict[str, int]:
    """Count applicable articles by outcome.

    :param matrix: Article → verdict mapping (paragraph rows are skipped).
    :returns: ``met`` / ``attention`` / ``unmet`` / ``unknown`` / ``total``.
    """
    counts = {"met": 0, "attention": 0, "unmet": 0, "unknown": 0, "total": 0}
    for verdict in article_rows(matrix).values():
        v = str(verdict).upper()
        if v in NOT_SCORED:
            continue
        counts["total"] += 1
        key = {"PASS": "met", "PASS_WITH_OBSERVATIONS": "attention",
               "FAIL": "unmet"}.get(v, "unknown")
        counts[key] += 1
    return counts


def render_kpis(final: dict) -> None:
    """Render the dashboard statistics row.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    tiles = kpi_tiles(final, matrix_counts(final.get("compliance_matrix") or {}))
    st.markdown(f'<div class="aaa-tiles">{"".join(tiles)}</div>', unsafe_allow_html=True)
