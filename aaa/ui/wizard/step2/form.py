"""Question widgets for wizard step 2 (rendered inside the form context)."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.constants import ANNEX_III_LABELS
from aaa.ui.wizard.step2.form2 import render_questions_5_to_8

#: How many numbered prompts step 2 renders, across both halves of the form.
#: Written once and used in the heading, because M25 was a hand-counted heading
#: that had drifted from the questions below it.
QUESTION_COUNT = 9

_ENTITY_OPTIONS = ["provider", "deployer", "distributor", "importer",
                   "product_manufacturer", "authorised_representative"]


def render_questions() -> dict:
    """Render the eight questionnaire widgets and return their values.

    Must be called inside an open ``st.form`` context.

    :returns: Mapping of questionnaire answers keyed by Stage A field name.
    """
    st.markdown("**1. What is your role in relation to this AI system?**")
    st.caption("Are you the company that built/trained the model (Provider), "
               "or deploying someone else's model (Deployer)?")
    entity_type = st.multiselect("Select all that apply", options=_ENTITY_OPTIONS,
                                 default=[], key="q_entity_type")

    st.markdown("**2. Who are the end users of this system?**")
    st.caption("B2B = sold to businesses, B2C = used by consumers directly, "
               "Public Sector = government/public authority, Internal = only within your organisation.")
    # No preselection (T-20260914-021): an untouched "b2b" was recorded as the
    # provider's answer. Unanswered, step 3 asks again and blocks the run.
    deployment_context = st.selectbox("Deployment context", options=["b2b", "b2c", "public_sector", "internal"],
                                      index=None, placeholder="Choose one", key="q_deployment_context",
                                      label_visibility="collapsed")

    st.markdown("**3. Does this system process personal data?**")
    st.caption("Does it use or produce data that identifies individuals — names, IDs, locations, behaviour, etc.?")
    gdpr_overlap = st.checkbox("Yes, it processes personal data", key="q_gdpr_overlap")

    # M26: this used to render only `if gdpr_overlap`, inside `st.form`. A form
    # does not rerun when a widget inside it changes, so `gdpr_overlap` is always
    # the value from the *previous* submit — False on the only pass that matters.
    # The question was therefore unreachable, and `special_category_data` could
    # only ever be False from the wizard. Art. 10 §5 turns on this answer, and
    # this very engagement had a PII scan find racial-or-ethnic-origin proxies
    # the declaration denied. Always asked; the caption carries the condition
    # that the `if` used to.
    st.markdown("**3a. Does it process special-category data?**")
    st.caption("Only if it processes personal data. Health records, biometrics, "
               "political or religious beliefs, racial/ethnic origin — see GDPR Art. 9.")
    special_category_data = st.checkbox(
        "Yes, it processes special-category data", key="q_special_category")

    special_category_data = special_category_data and gdpr_overlap
    part2 = render_questions_5_to_8()
    keys = list(ANNEX_III_LABELS.keys())
    values = list(ANNEX_III_LABELS.values())
    return {
        "entity_type": entity_type,
        "deployment_context": deployment_context,
        "gdpr_overlap": gdpr_overlap,
        "special_category_data": special_category_data,
        "gpai_general_purpose": part2["gpai"],
        "declared_annex_iii_sections": [keys[values.index(lbl)] for lbl in part2["annex_labels"]],
        "provider_elects_third_party": part2["third_party"],
        "territorial_scope": part2["territorial_scope"],
        # Not a Stage A field of its own: it decides whether
        # `derive_component_modalities` declares a second, discriminative
        # component, which is what keeps Phases 3 and 4 in the plan.
        "has_ranking_component": part2["has_ranking_component"],
    }
