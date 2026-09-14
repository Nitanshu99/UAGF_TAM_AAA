"""Wizard step 3 — the review form (Stage A + Stage B).

Since the wizard stopped spending an LLM call pre-filling this page, it is the
whole job rather than a proofread, so it is organised for someone working
through it: a checklist of what is still missing and what each gap is worth,
then three tabs instead of one forty-field scroll.

The widget keys are untouched. ``collect_stage_a`` / ``collect_stage_b`` read
``s3_*`` out of session state and produce exactly the payloads they did before —
this changes where a field is rendered, never what it is called.
"""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.styles import section_title
from aaa.ui.wizard.collect import collect_stage_a, collect_stage_b  # noqa: F401
from aaa.ui.wizard.loaders import load_schema  # noqa: F401
from aaa.ui.wizard.step3.checklist import render_checklist  # noqa: F401
from aaa.ui.wizard.step3.data_dict import render_data_dictionary  # noqa: F401
from aaa.ui.wizard.step3.header import render_score_and_gate  # noqa: F401
from aaa.ui.wizard.step3.model_meta import render_model_meta  # noqa: F401
from aaa.ui.wizard.step3.nav import render_navigation  # noqa: F401
from aaa.ui.wizard.step3.panels import _render_about, _render_dossier
from aaa.ui.wizard.step3.prior_assessment import render_prior_assessment  # noqa: F401
from aaa.ui.wizard.step3.provenance import render_provenance  # noqa: F401
from aaa.ui.wizard.step3.stage_a import render_identity  # noqa: F401
from aaa.ui.wizard.step3.stage_a.classification import render_classification  # noqa: F401
from aaa.ui.wizard.step3.stage_a.flags import render_flags  # noqa: F401
from aaa.ui.wizard.step3.stage_a.fli import render_fli_fields  # noqa: F401
from aaa.ui.wizard.step3.stage_b import (  # noqa: F401
    render_descriptions,
    render_metrics_and_standards,
)
from aaa.ui.wizard.step3.state import initialise_step3_state  # noqa: F401
from aaa.ui.wizard.step3.uploads import render_uploads  # noqa: F401


def render_step_3() -> None:
    """Render the review form with live completeness scoring."""
    store: EvidenceStore = st.session_state["aaa_evidence_store"]
    eid: str = st.session_state["engagement_id"]
    questionnaire: dict = st.session_state.get("questionnaire_answers", {})

    initialise_step3_state(st.session_state.get("extraction_result", {}), questionnaire)
    section_title("Tell us about your system",
                  "This is the Annex IV dossier the EU AI Act requires. Work "
                  "through it in any order — the meter shows how close you are "
                  "to the 80% the audit needs to start.")
    score, gate, report = render_score_and_gate(collect_stage_a(), collect_stage_b())
    render_checklist(report)

    about, dossier, artefacts = st.tabs(
        ["Your system", "The dossier", "Documents, model & data"])
    with about:
        _render_about()
    with dossier:
        _render_dossier()
    with artefacts:
        render_uploads(store, eid)
        render_model_meta()
        render_provenance()
        render_data_dictionary()

    render_navigation(score, gate)
