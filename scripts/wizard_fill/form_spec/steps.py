"""Steps 0, 1 and 2, the step-3 tabs, and every button — label → what it sets."""
from __future__ import annotations

from aaa.ui.wizard.constants import ANNEX_III_LABELS
from aaa.ui.wizard.step2.form import _ENTITY_OPTIONS
from aaa.ui.wizard.step2.form2 import _TERRITORY_OPTIONS

#: Step 0 — label → the Stage A field it becomes.
STEP0_TEXT = {
    "Your company": "provider_name",
    "What the AI system is called": "system_name",
}

#: Step 1's uploaders. Their visible headings are separate ``st.markdown`` calls,
#: so the widget's own label — rendered with ``label_visibility="collapsed"`` — is
#: the only thing that identifies it.
STEP1_UPLOADERS = {"documents": "Upload documents", "model": "Upload model",
                   "dataset": "Upload datasets"}

#: Step 2 — checkbox label → the questionnaire answer it sets. Labels come from
#: ``step2.form`` / ``step2.form2``; keeping them here as data lets the driver
#: assert every one is on the page before it starts clicking.
STEP2_CHECKBOXES = {
    "Yes, it processes personal data": "gdpr_overlap",
    "Yes, it processes special-category data": "special_category_data",
    "Yes, this is a general-purpose AI model": "gpai_general_purpose",
    "Yes — it ranks, scores, matches or classifies": "has_ranking_component",
    "Yes, we elect voluntary third-party assessment": "provider_elects_third_party",
}

#: Step 2 — multiselect label → (Stage A field, the options it offers).
STEP2_MULTISELECTS = {
    "Select all that apply": ("entity_type", list(_ENTITY_OPTIONS)),
    "Annex III categories": ("declared_annex_iii_sections", list(ANNEX_III_LABELS.values())),
    "Territory": ("territorial_scope", list(_TERRITORY_OPTIONS)),
}

#: Step 2 — selectbox label → the questionnaire answer it sets. It starts with
#: no option chosen (T-20260914-021), so the driver has to answer it.
STEP2_SELECTS = {"Deployment context": "deployment_context"}

#: Step 3's three tabs, in the order ``render_step_3`` creates them. An
#: inactive tab's panel is in the DOM but not visible, so every section has to
#: be preceded by its tab.
TABS = {"stage_a": "Your system", "stage_b": "The dossier",
        "documents": "Documents, model & data"}

#: Buttons, by the label their module renders.
BUTTONS = {
    "start": "Start my audit",
    "skip_uploads": "Continue without them",
    "file_uploads": "File my documents",
    "step2_submit": "Continue",
    "run": "Confirm & run my audit",
}

__all__ = ["BUTTONS", "STEP0_TEXT", "STEP1_UPLOADERS", "STEP2_CHECKBOXES",
           "STEP2_MULTISELECTS", "STEP2_SELECTS", "TABS"]
