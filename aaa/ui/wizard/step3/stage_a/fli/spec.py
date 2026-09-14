"""Widget specification for the FLI advanced compliance fields."""
from __future__ import annotations

#: label → (session key, options) for the FLI multiselect widgets.
_MULTISELECTS: dict[str, tuple[str, list[str]]] = {
    "FLI-E2 · Art. 25 modifications (triggers Provider status)": (
        "s3_a_art25_status_change",
        ["name_trademark", "intended_purpose_change", "substantial_modification", "none"]),
    "FLI-HR1 · Annex I Section B sectoral categories": (
        "s3_a_annex_i_section_b",
        ["civil_aviation_security", "two_three_wheel_vehicles", "agricultural_forestry_vehicles",
         "marine_equipment", "rail_interoperability", "motor_vehicles", "civil_aviation"]),
    "FLI-HR2 · Annex I Section A product categories": (
        "s3_a_annex_i_section_a",
        ["machinery", "toys", "recreational_craft", "lifts", "atex_equipment", "radio_equipment",
         "pressure_equipment", "cableway", "ppe", "gas_appliances", "medical_devices",
         "ivd_medical_devices"]),
    "FLI-R3 · Art. 5 prohibited practices (any selection halts engagement)": (
        "s3_a_art5_prohibited_practices",
        ["subliminal_manipulation", "exploit_vulnerabilities", "biometric_categorisation",
         "social_scoring", "predictive_policing", "facial_recognition_db_scraping",
         "emotion_recognition_workplace_education", "real_time_remote_biometrics", "none"]),
    "FLI-R4 · Art. 50 transparency triggers": (
        "s3_a_art50_transparency_triggers",
        ["deepfake_content", "public_interest_text", "emotion_or_biometric_categorisation",
         "direct_interaction_with_persons", "synthetic_content_generation", "none"]),
}

_EXCLUSION_OPTIONS = ["", "military", "third_country_law_enforcement",
                      "research_and_development", "open_source", "personal_use", "none"]
