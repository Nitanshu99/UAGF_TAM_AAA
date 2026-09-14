"""Severity-grouped findings for the results page (Sentinel-style layout).

Material findings render open; possibly-material and observations collapse
into expanders so the page stays scannable.
"""
from __future__ import annotations

import streamlit as st

from aaa.ui import styles

_GROUPS = (("material", "Material findings", True),
           ("possibly_material", "Possibly material findings", False),
           ("observation", "Observations", False))


def render_findings(final: dict) -> None:
    """Render blocking findings by severity, then positive findings.

    :param final: Final ``AuditState`` dictionary.
    :type final: dict
    """
    blocking = final.get("blocking_findings") or []
    if blocking:
        styles.section_title(f"Findings ({len(blocking)})",
                             "Issues raised during the audit, ordered by materiality.")
        for severity, label, expanded in _GROUPS:
            group = [f for f in blocking if f.get("materiality") == severity]
            if not group:
                continue
            if expanded:
                for i, finding in enumerate(group):
                    styles.finding_row(finding, i)
            else:
                with st.expander(f"{label} ({len(group)})", expanded=False):
                    for i, finding in enumerate(group):
                        styles.finding_row(finding, i)
    positives = final.get("positive_findings") or []
    if positives:
        with st.expander(f"Positive findings ({len(positives)})", expanded=False):
            for finding in positives:
                st.markdown(
                    f"✅ **{finding.get('finding_id', '')}** — "
                    f"{finding.get('description', '')}")
