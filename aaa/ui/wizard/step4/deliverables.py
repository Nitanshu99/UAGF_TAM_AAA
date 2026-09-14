"""What the customer actually takes away: two PDFs, and nothing else.

The results page used to hand over four downloads, two of which were
``eng-06_T18.json`` and ``eng-06_T17.json``. A T-number is an internal template
id; a customer offered one has been handed our filing system and asked to work
out which file is their report. Both JSON artefacts and the raw AuditState now
live in the admin console, where the people who know what a T18 is can get them.

What is left is the audit report and the plain-language brief — the two
documents written to be read.
"""
from __future__ import annotations

import logging

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.styles import section_title
from aaa.ui.wizard.step4.artefacts import client_brief_markdown
from aaa.ui.wizard.step4.documents import _formal_report, _plain_language

logger = logging.getLogger(__name__)






def render_deliverables(eid: str, final: dict, store: EvidenceStore,
                        degraded: bool) -> None:
    """Render the customer's two documents.

    :param eid: Engagement identifier.
    :param final: Final ``AuditState`` dictionary.
    :param store: Evidence store holding the rendered artefacts.
    :param degraded: Whether this run is unfit to hand over.
    """
    if degraded:
        # The heading below promises two documents. On a degraded run there are
        # none, so it does not get printed — the banner above has already said
        # why, and repeating it here in different words reads as two problems.
        section_title("Your documents",
                      "Held back until this audit has been re-run. Nothing is "
                      "needed from you.")
        return
    section_title("Your documents",
                  "Both are yours to keep, share with your notified body, and "
                  "file as evidence of the assessment.")
    left, right = st.columns(2, gap="medium")
    with left, st.container(key="aaacard-brief"):
        _plain_language(eid, client_brief_markdown(final, store))
    with right, st.container(key="aaacard-formal"):
        _formal_report(eid, final, store)
