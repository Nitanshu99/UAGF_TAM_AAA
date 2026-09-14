"""Tell the customer what we found on file, in place of asking them for it.

Removing the "CGSA assessment ID" input fixed the wrong question but left the
customer with no sign that a prior self-assessment exists or that it matters,
and it does: it is the evidence Phase 5 reviews for Arts. 9, 12, 14, 17 and 72.
So the field is replaced by a statement of what we found — named for what it is
to them, a governance self-assessment, never by its identifier.

What we found is not one thing. An **evaluated** export carries a threshold on
every control, so a control below it becomes a finding in their report; a
**self-assessment** export carries scores and prose only, and cannot produce a
finding at all. Those are materially different audits, and on 2026-09-11 the
difference passed unremarked through the whole pipeline — six articles came back
softer with nothing on screen to say why. It is stated here in the customer's
own terms rather than left for them to discover in the verdicts.
"""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui.styles import note
from aaa.ui.wizard.collect.cgsa import prior_assessment_profile


def render_prior_assessment() -> None:
    """State whether a governance self-assessment was found, and what it supports."""
    provider = str(st.session_state.get("s3_a_provider_name") or "").strip()
    if not provider:
        # Nothing has been typed yet; a "nothing found" notice here would be
        # about the empty form, not about the client.
        return
    profile = prior_assessment_profile()
    if profile is None:
        note("info", "i", "No earlier governance self-assessment on file",
             "We could not find a previous assessment filed under this provider "
             "and system name. Your audit will run from the documents you supply "
             "instead, and the report will say where that left a gap.")
        return
    if profile.get("evaluated"):
        note("ok", "✓", "We found your governance self-assessment",
             f"{html.escape(provider)} has one on file, independently scored, and "
             "we have attached it to this audit. Its findings feed the "
             "risk-management, oversight and monitoring sections of your report — "
             "there is nothing for you to upload or enter.")
        return
    note("warn", "!", "We found your governance self-assessment — unscored",
         f"{html.escape(provider)} has one on file and we have attached it, but it "
         "records what your team reported rather than what an assessor checked, so "
         "on its own it cannot show a gap. Sections that would normally draw on it "
         "will lean on the documents you supply instead.")
