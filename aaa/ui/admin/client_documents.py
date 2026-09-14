"""The client uploads listed in the admin console."""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.wizard.step4.artefacts import client_brief_markdown, customer_pdf, report_pdf


def _client_documents(left, right, eid: str, final: dict, store: EvidenceStore,
                      suffix: str) -> None:
    """Render the two customer PDFs, in the admin console's plainer terms."""
    with left:
        pdf = customer_pdf(eid, final) or report_pdf(final, store)
        if pdf is None:
            st.caption("Formal report PDF: not produced.")
        else:
            st.download_button("⬇ Formal conformity report (PDF)", data=pdf,
                               file_name=f"{eid}{suffix}_audit_report.pdf",
                               mime="application/pdf")
    with right:
        markdown = client_brief_markdown(final, store)
        if markdown is None:
            st.caption("Client brief: not produced for this run.")
            return
        st.download_button("⬇ Client brief (Markdown source)",
                           data=markdown.encode("utf-8"),
                           file_name=f"{eid}{suffix}_plain_language_report.md",
                           mime="text/markdown")


__all__ = ["_client_documents"]
