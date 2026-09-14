"""The remediation roadmap, as a to-do list rather than a governance artefact."""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui.styles import section_title

#: Roadmap severity → the pill tone that names the urgency.
_SEVERITY_TONE = {"critical": "is-bad", "high": "is-bad",
                  "medium": "is-warn", "low": "is-info"}


def _item(entry: dict, index: int) -> str:
    """One numbered action with its deadline and the articles behind it."""
    severity = str(entry.get("gap_severity") or "medium").lower()
    weeks = entry.get("deadline_weeks")
    when = (f"Within {weeks} weeks" if weeks else
            str(entry.get("priority_label") or "").replace("_", " ").title() or "Scheduled")
    action = html.escape(str(entry.get("recommended_action") or entry.get("gap_detail") or ""))
    return (f'<div class="aaa-article-row" style="--i:{min(index, 8)}">'
            f'<div><div class="subject">{index + 1}. {action}</div>'
            f'<div class="ref">{html.escape(when)}'
            f'{" · " + html.escape(str(entry.get("control_id"))) if entry.get("control_id") else ""}'
            f'</div></div>'
            f'<div><span class="aaa-pill {_SEVERITY_TONE.get(severity, "is-warn")}">'
            f"{html.escape(severity.title())}</span></div></div>")


def render_next_steps(final: dict) -> None:
    """Render the ranked remediation actions.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    roadmap = [e for e in (final.get("remediation_roadmap") or []) if isinstance(e, dict)]
    if not roadmap:
        return
    section_title("What to do next",
                  "Ordered by how much each one moves your conformity. "
                  "Your report explains the reasoning behind every entry.")
    ranked = sorted(roadmap, key=lambda e: e.get("rank") or 99)[:6]
    st.markdown(
        '<div class="aaa-card aaa-rise">'
        + "".join(_item(entry, i) for i, entry in enumerate(ranked))
        + "</div>", unsafe_allow_html=True)
