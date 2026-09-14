"""Explainability/fairness and security/robustness status panel for step 4.

Compact companion to :mod:`aaa.tools.report_render.pdf.evidence` — shows
whether each section was gated out, failed, or produced evidence, without
duplicating the PDF's full artefact table on the dashboard.
"""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui import styles

#: evidence_source → (pill tone, status label)
_STATUS = {
    "internal": ("is-none", "internal analysis"),
    "external": ("is-info", "partner analysis"),
    "not_required": ("is-ok", "not required"),
}


def _status_line(evidence: dict | None) -> str:
    """Render one status badge + detail line for an evidence document."""
    evidence = evidence or {}
    source = evidence.get("evidence_source") or ""
    cls, label = _STATUS.get(source, ("is-none", "no evidence"))
    badge = f'<span class="aaa-pill {cls}">{html.escape(label)}</span>'
    if source == "not_required":
        return f"{badge} &nbsp;{html.escape(evidence.get('reason', ''))}"
    if evidence.get("error"):
        return f"{badge} &nbsp;Evidence could not be collected during this run."
    return badge


def render_evidence_status(final: dict) -> None:
    """Render the Art. 13 / Art. 15 evidence status panel.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    if "xai_evidence" not in final and "security_evidence" not in final:
        return
    styles.section_title("Explainability & security evidence",
                         "Status of the Art. 13 and Art. 15 independent-analysis evidence.")
    st.markdown(
        '<div class="aaa-card">'
        f'<div><b>Explainability & fairness (Art. 13):</b> '
        f'{_status_line(final.get("xai_evidence"))}</div>'
        f'<div style="margin-top:.4rem;"><b>Security & robustness (Art. 15):</b> '
        f'{_status_line(final.get("security_evidence"))}</div>'
        '</div>', unsafe_allow_html=True)
