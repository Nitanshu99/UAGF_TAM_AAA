"""What is still missing, named in the customer's words and ranked by value.

The form has around forty inputs. Exactly fourteen of them, across the nine
Annex IV sections, move the 0.80 completeness gate — and the sections are not
worth the same: §1 is worth 0.20, §8 and §9 are worth 0.05 each. A customer
looking at forty boxes and a percentage has no way to know that, so they either
fill in everything or give up.

This panel reads the real :func:`intake_completeness_calculator` report — the
same one the gate uses — and says which sections are short and what each is
worth, heaviest first.
"""
from __future__ import annotations

import html

import streamlit as st

from aaa.tools.intake_completeness_calculator.section_weights import SECTION_WEIGHTS

#: Annex IV section → (what a customer would call it, where they will find it).
SECTION_LABELS: dict[int, tuple[str, str]] = {
    1: ("What the system is and does", "Your system"),
    2: ("How it was built and trained", "The dossier"),
    3: ("Monitoring and logging", "The dossier"),
    4: ("Performance metrics", "The dossier"),
    5: ("Risk management file", "Documents"),
    6: ("Changes since launch", "The dossier"),
    7: ("Standards applied", "The dossier"),
    8: ("EU declaration of conformity", "Documents"),
    9: ("Post-market monitoring plan", "Documents"),
}


def _gaps(report) -> list[tuple[int, float, float]]:
    """Sections that are not yet complete, worth the most first.

    :param report: A ``CompletenessReport``.
    :returns: ``(section, fraction_done, points_still_available)`` tuples.
    """
    gaps = []
    for key, section in report.section_scores.items():
        if section.score >= 1.0:
            continue
        available = SECTION_WEIGHTS.get(int(key), section.weight) * (1.0 - section.score)
        gaps.append((int(key), section.score, available))
    return sorted(gaps, key=lambda g: g[2], reverse=True)


def _row(section: int, done: float, points: float) -> str:
    """One outstanding section: what it is, where it is, what it is worth."""
    label, where = SECTION_LABELS.get(section, (f"Annex IV §{section}", ""))
    return (f'<div class="aaa-article-row">'
            f'<div><div class="subject">{html.escape(label)}</div>'
            f'<div class="ref">Annex IV §{section} · under “{html.escape(where)}”'
            f'{" · part-filled" if done else ""}</div></div>'
            f'<div><span class="aaa-pill is-info">+{points * 100:.0f} points</span></div>'
            "</div>")


def render_checklist(report) -> None:
    """Render the outstanding-sections panel above the form.

    :param report: A ``CompletenessReport``, or ``None`` when unavailable.
    """
    if report is None:
        return
    gaps = _gaps(report)
    if not gaps:
        return
    shortfall = max(0.0, 0.80 - report.score)
    lead = ("You have enough to run the audit. Anything below is optional depth."
            if shortfall <= 0 else
            f"You need {shortfall * 100:.0f} more points to start. "
            "These are worth the most:")
    st.markdown(
        f'<div class="aaa-card aaa-rise" style="margin-block-end:1.4rem">'
        f'<div class="aaa-eyebrow">What is still missing</div>'
        f'<p class="aaa-section-sub" role="status" style="margin:.35rem 0 .6rem">'
        f"{html.escape(lead)}</p>"
        + "".join(_row(s, d, p) for s, d, p in gaps[:5])
        + "</div>", unsafe_allow_html=True)
