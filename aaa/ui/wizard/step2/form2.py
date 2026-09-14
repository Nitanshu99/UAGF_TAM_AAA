"""Questions 5–8 of the wizard step-2 form."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.constants import ANNEX_III_LABELS

_TERRITORY_OPTIONS = ["placed_on_eu_market", "gpai_placed_on_eu_market", "established_in_eu",
                      "importer_in_eu", "output_used_in_eu", "none"]


def render_questions_5_to_8() -> dict:
    """Render questions 5–8 inside the open form context.

    :returns: Partial answers: gpai flag, the composite-routing answer,
        annex labels, third-party, territory.
    """
    st.markdown("**4. Is this a General-Purpose AI (GPAI) model?**")
    st.caption("A foundation model or LLM designed for many different tasks, "
               "not one specific use case (Arts. 51–55 EU AI Act).")
    gpai = st.checkbox("Yes, this is a general-purpose AI model", key="q_gpai")

    # §6.2 composite routing. The phase plan is solved from the declaration
    # before any phase dispatches: a system declared purely generative skips
    # model validation and output fairness, and no document states component
    # structure reliably enough to infer it with confidence. Only the customer
    # knows, so only the customer can be asked.
    st.markdown("**4a. Does your system also rank, score, match or classify?**")
    st.caption("Many systems pair a language model with a part that sorts or "
               "scores people, applications or items — a shortlist, a match, a "
               "risk band. If yours does, we audit that part too, for accuracy "
               "and for bias.")
    has_ranking = st.checkbox(
        "Yes — it ranks, scores, matches or classifies", key="q_has_ranking_component")

    st.markdown("**5. Does this system fall under any Annex III high-risk categories?**")
    st.caption("Select any categories that apply to your system's use case.")
    annex_labels = st.multiselect("Annex III categories", options=list(ANNEX_III_LABELS.values()),
                                  default=[], key="q_annex_iii", label_visibility="collapsed")

    st.markdown("**6. Are you electing a voluntary third-party conformity assessment?**")
    st.caption("Choose to have a notified body independently verify compliance, "
               "even if not legally required (Art. 43 §1(b)).")
    third_party = st.checkbox("Yes, we elect voluntary third-party assessment", key="q_third_party")

    st.markdown("**7. Where is this system placed on the market or used?**")
    st.caption("Select all territories that apply for EU AI Act coverage.")
    territorial_scope = st.multiselect("Territory", options=_TERRITORY_OPTIONS, default=[],
                                       key="q_territorial_scope", label_visibility="collapsed")

    return {"gpai": gpai, "annex_labels": annex_labels,
            "third_party": third_party, "territorial_scope": territorial_scope,
            "has_ranking_component": has_ranking}
