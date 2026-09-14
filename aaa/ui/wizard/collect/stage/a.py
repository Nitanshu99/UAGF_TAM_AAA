"""Stage A payload collector (reads wizard widget session state)."""
from __future__ import annotations

from typing import Any

import streamlit as st

from aaa.platform.state.contacts import CONTACT_ROLES, declared_contacts
from aaa.ui.wizard.collect.cgsa import prior_assessment_id
from aaa.ui.wizard.collect.modalities import derive_component_modalities
from aaa.ui.wizard.parsing import normalise_version

#: Stage A session keys collected verbatim: key → default. The three enum
#: declarations default to ``None`` — undeclared, which blocks the run — never to
#: an option the provider did not choose (T-20260914-021).
_STAGE_A_DEFAULTS: dict[str, Any] = {
    "provider_name": "", "system_name": "", "intended_purpose": "",
    "declared_modality": None, "declared_risk_tier": None,
    "declared_annex_iii_sections": [], "deployment_context": None,
    "provider_elects_third_party": False, "gdpr_overlap": False,
    "gpai_general_purpose": False, "special_category_data": False,
    "entity_type": [], "territorial_scope": [], "art25_status_change": [],
    "annex_i_section_a": [], "annex_i_section_b": [],
    "third_party_ca_legally_required": False, "art6_derogation_claimed": False,
    "gpai_systemic_risk": False, "art5_prohibited_practices": [],
    "art50_transparency_triggers": [], "is_public_body_or_public_service": False,
}


def collect_stage_a() -> dict:
    """Assemble the Stage A declaration payload from session state.

    :returns: Stage A dictionary matching the T01a schema.
    """
    s = st.session_state
    payload: dict[str, Any] = {
        key: s.get(f"s3_a_{key}", default) for key, default in _STAGE_A_DEFAULTS.items()
    }
    payload["version"] = normalise_version(s.get("s3_a_version"))
    payload["art43_preview"] = None
    # The customer is never asked for this. The CGSA is filed by S4 against the
    # organisation and system it describes, and those are the two things step 0
    # already collected, so the id is ours to look up rather than theirs to
    # quote. A session value still wins where one exists — the API and CLI
    # entry points declare it directly.
    payload["cgsa_assessment_id"] = prior_assessment_id()
    payload["art6_derogation_rationale"] = s.get("s3_a_art6_derogation_rationale") or None
    payload["art2_exclusion"] = s.get("s3_a_art2_exclusion") or None
    contacts = declared_contacts({role: s.get(f"s3_a_contact_{role}") for role in CONTACT_ROLES})
    if contacts:
        payload["organisation_contacts"] = contacts
    # §6.2 composite routing. The phase plan is solved from this declaration
    # before any phase dispatches, and a generative-only declaration skips model
    # validation and output fairness. A wizard that cannot say "it also ranks
    # things" therefore silently descopes two phases — which is what case 06 did.
    # Read from `questionnaire_answers`, never from the `q_*` widget key:
    # Streamlit drops a widget's key once that widget stops rendering, and by
    # step 3 step 2's checkbox is long gone (M24, M28). `.get` returning None
    # means "never asked", which falls back to the dossier signals.
    from aaa.ui.wizard.collect.stage.b import collect_stage_b
    answers = s.get("questionnaire_answers") or {}
    components = derive_component_modalities(
        payload["declared_modality"], collect_stage_b(),
        answers.get("has_ranking_component"))
    if components:
        payload["component_modalities"] = components
    return payload
