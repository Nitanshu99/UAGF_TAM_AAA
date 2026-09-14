"""The two customer documents the results page offers, each with its own download."""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.wizard.step4.artefacts import customer_pdf, report_pdf
from aaa.ui.wizard.step4.cards import _brief_pdf, _heading


def _plain_language(eid: str, brief_md: str | None) -> None:
    """The brief written for the customer, offered first because it is theirs."""
    _heading("📘", "Your audit report",
             "Written in plain language: what we checked, what we found, and "
             "what it means for you. Start here.")
    pdf = _brief_pdf(eid, brief_md)
    if pdf is not None:
        st.download_button("Download report (PDF)", data=pdf,
                           file_name=f"{eid}_plain_language_report.pdf",
                           mime="application/pdf", type="primary")
    elif brief_md is not None:
        st.download_button("Download report (Markdown)", data=brief_md.encode("utf-8"),
                           file_name=f"{eid}_plain_language_report.md",
                           mime="text/markdown", type="primary")
    else:
        st.markdown('<p class="aaa-muted">Not produced for this run — the formal '
                    "report beside it covers the same findings.</p>",
                    unsafe_allow_html=True)
def _formal_report(eid: str, final: dict, store: EvidenceStore) -> None:
    """The signed conformity report, for the compliance file."""
    _heading("📑", "Formal conformity report",
             "The full audit opinion with evidence references, for your "
             "technical file or a notified body.")
    pdf = customer_pdf(eid, final) or report_pdf(final, store)
    if pdf is None:
        st.markdown('<p class="aaa-muted">Not available for this run.</p>',
                    unsafe_allow_html=True)
        return
    st.download_button("Download formal report (PDF)", data=pdf,
                       file_name=f"{eid}_audit_report.pdf",
                       mime="application/pdf")


__all__ = ["_formal_report", "_plain_language"]
