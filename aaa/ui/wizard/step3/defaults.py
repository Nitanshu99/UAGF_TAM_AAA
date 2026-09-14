"""Default seed values for wizard step 3 session-state keys."""
from __future__ import annotations

#: Stage A text fields seeded from the extraction result: key → default.
#: ``cgsa_assessment_id`` is deliberately absent: no widget collects it and
#: ``collect_stage_a`` looks it up from the provider and system names instead,
#: so seeding an empty string here would only add a key nothing writes.
#: The version, modality and risk tier start undeclared (T-20260914-021): a
#: preselected ``0.1.0`` / ``tabular`` / ``limited`` submitted unchanged became the
#: provider's own declaration. An undeclared one blocks the run until chosen.
EXTRACTED_A = {"provider_name": "", "system_name": "", "version": "",
               "intended_purpose": "", "declared_modality": None,
               "declared_risk_tier": None}

#: Stage A fields seeded from the questionnaire: key → default. The deployment
#: context starts undeclared for the same reason as the modality above.
QUESTIONNAIRE_A = {"deployment_context": None, "gdpr_overlap": False,
                   "special_category_data": False, "gpai_general_purpose": False,
                   "declared_annex_iii_sections": [], "provider_elects_third_party": False,
                   "entity_type": [], "territorial_scope": []}

#: Advanced (FLI) fields initialised empty: key → default.
ADVANCED_A = {"art25_status_change": [], "annex_i_section_a": [], "annex_i_section_b": [],
              "third_party_ca_legally_required": False, "art6_derogation_claimed": False,
              "art6_derogation_rationale": "", "gpai_systemic_risk": False, "art2_exclusion": "",
              "art5_prohibited_practices": [], "art50_transparency_triggers": [],
              "is_public_body_or_public_service": False}

#: Stage B free-text fields seeded from the extraction result.
EXTRACTED_B = ("general_description", "model_type", "design_process",
               "training_data_description", "data_governance_measures",
               "monitoring_measures", "logging_capabilities")
