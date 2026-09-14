"""The about and dossier panels the step-3 tabs are built from."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.loaders import load_schema
from aaa.ui.wizard.step3.prior_assessment import render_prior_assessment
from aaa.ui.wizard.step3.stage_a import render_identity
from aaa.ui.wizard.step3.stage_a.classification import render_classification
from aaa.ui.wizard.step3.stage_a.contacts import render_contacts
from aaa.ui.wizard.step3.stage_a.flags import render_flags
from aaa.ui.wizard.step3.stage_a.fli import render_fli_fields
from aaa.ui.wizard.step3.stage_b import render_descriptions, render_metrics_and_standards

#: Extraction no longer runs from the wizard, so no field carries a confidence
#: or a source. Passed through rather than removed from the render signatures:
#: the ``/extract-triage`` endpoint still produces them, and re-enabling
#: pre-fill should not mean rebuilding fifteen call sites.
_NO_PROVENANCE: tuple[dict, dict, list] = ({}, {}, [])
def _render_about() -> None:
    """Stage A — who you are, what the system is, how it is classified."""
    confidence, sources, missing = _NO_PROVENANCE
    render_identity(confidence, sources, missing)
    render_prior_assessment()
    schema_props = load_schema("T01a_stage_a_triage.json").get("properties", {})
    render_classification(schema_props, confidence, sources, missing)
    with st.expander("Advanced classification flags", expanded=False):
        render_flags()
        render_fli_fields()
    render_contacts()
def _render_dossier() -> None:
    """Stage B — the nine Annex IV sections' free-text and metric fields."""
    confidence, sources, missing = _NO_PROVENANCE
    render_descriptions(confidence, sources, missing)
    render_metrics_and_standards(confidence, sources, missing)


__all__ = ["_NO_PROVENANCE", "_render_about", "_render_dossier"]
