"""Wizard step 0 — the welcome screen.

The customer used to be asked for an "Engagement ID" here, pre-filled with
``eng-777b6688``. It is the auditor's filing reference, it means nothing to the
person starting an audit, and being asked to invent one is the first thing the
product ever said to them. It is now derived from their company name behind the
scenes (:func:`new_engagement_id`) and never shown until the results page,
where it exists so they can quote it to us.

What the screen asks for instead is the two things the customer certainly
knows and Stage A certainly requires: who they are and what the system is
called. Asked once, here, they are not asked again on the review form.
"""
from __future__ import annotations

import re
import uuid

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.styles import hero
from aaa.ui.wizard.step0.panels import render_panels

_SLUG = re.compile(r"[^a-z0-9]+")


def new_engagement_id(company: str) -> str:
    """Derive a filing reference from *company* plus a short random suffix.

    :param company: The company name as typed. May be blank.
    :returns: An id of the form ``eng-acme-gmbh-1a2b3c``, unique per run.
    """
    slug = _SLUG.sub("-", company.strip().lower()).strip("-")[:32]
    return f"eng-{slug}-{uuid.uuid4().hex[:6]}" if slug else f"eng-{uuid.uuid4().hex[:8]}"


def render_step_0() -> None:
    """Render the landing page and create the engagement on submit."""
    hero(
        "EU AI Act conformity audit",
        "Let's find out where your AI system stands.",
        "Share the documents you already have, answer a few questions about "
        "how the system is used, and we audit it against every EU AI Act "
        "article that applies. You get a report you can act on.",
        ["No compliance expertise needed", "Around 30 minutes",
         "Your documents stay private"])
    render_panels()
    st.markdown('<div style="margin-block:2.2rem .6rem">'
                '<h2 class="aaa-section-title">Tell us who you are</h2>'
                '<div class="aaa-section-sub">Two details, so the report has your '
                "name on it. Everything else we work out from your documents."
                "</div></div>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="medium")
    left.text_input("Your company", key="step0_company",
                    placeholder="e.g. Acme Analytics GmbH")
    right.text_input("What the AI system is called", key="step0_system",
                     placeholder="e.g. CreditScore")
    st.write("")
    # The button is deliberately never disabled. `st.text_input` returns "" until
    # the field is blurred, so gating on its return value gives a customer who
    # types their name and clicks straight through a button that does nothing on
    # the first click — the worst possible first interaction with the product.
    # Validating on submit, against session state (which the blur has by then
    # committed), means one click always does something.
    if st.button("Start my audit  →", type="primary"):
        company = str(st.session_state.get("step0_company") or "").strip()
        if not company:
            st.warning("We need your company name — it goes on the report.")
            return
        _begin(company, str(st.session_state.get("step0_system") or "").strip())


def _begin(company: str, system: str) -> None:
    """Create the engagement and advance to the upload step."""
    st.session_state["engagement_id"] = new_engagement_id(company)
    # Seeded into step 3's widget keys by `initialise_step3_state`, which treats
    # what the customer typed as outranking what the extractor guessed.
    st.session_state["intake_identity"] = {
        "provider_name": company, "system_name": system}
    if "aaa_evidence_store" not in st.session_state:
        st.session_state["aaa_evidence_store"] = EvidenceStore()
    st.session_state["step"] = 1
    st.rerun()
