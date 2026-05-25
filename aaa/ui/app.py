"""
aaa.ui.app — Streamlit demo UI for the AAA pipeline (§10, §11).

Wizard flow:

  1. **Stage A — Triage form** (≈20 fields, schema = T01a).
  2. **Stage B — Annex IV dossier** (URIs and §1–§9 metadata, schema = T01b).
  3. **Live completeness score** — runs ``intake_completeness_calculator``
     after every form change; gate at 0.80.
  4. **Run full audit** — calls IntakeValidator → Orchestrator; streams
     phase progress; displays final verdict and KPIs.
  5. **Downloads** — JSON summary + T17 compliance matrix + T18 audit report.

Run::

    pip install streamlit
    AAA_OFFLINE_MODE=true \
    CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
    streamlit run aaa/ui/app.py
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from typing import Any

# Repo root on path so ``aaa.*`` imports work when launched via streamlit run.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st  # noqa: E402

from aaa.agents.base import IntakeDispatch  # noqa: E402
from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError  # noqa: E402
from aaa.agents.tier1.orchestrator import Orchestrator  # noqa: E402
from aaa.platform.evidence import EvidenceStore  # noqa: E402
from aaa.tools.intake_completeness_calculator import (  # noqa: E402
    intake_completeness_calculator,
)
from aaa.tools.scope_gate import scope_gate  # noqa: E402

# Reference URL for FLI tooltips ("why this matters" links).
_FLI_REF = "https://artificialintelligenceact.eu/assessment/eu-ai-act-compliance-checker/"

_TEMPLATES_DIR = REPO_ROOT / "templates"
_FIXTURE_DIR = REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit"


# ---------------------------------------------------------------------------
# Form schemas (loaded lazily)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _load_schema(name: str) -> dict:
    return json.loads((_TEMPLATES_DIR / name).read_text())


@st.cache_data(show_spinner=False)
def _load_fixture(name: str) -> dict:
    path = _FIXTURE_DIR / name
    return json.loads(path.read_text()) if path.exists() else {}


# ---------------------------------------------------------------------------
# Stage A form
# ---------------------------------------------------------------------------

def _render_stage_a(defaults: dict) -> dict:
    """Render Stage A (T01a) form and return the payload.

    Field descriptions and tooltip wording are drawn from the FLI
    "EU AI Act Compliance Checker" v1.0 and from the T01a JSON Schema.
    """
    schema = _load_schema("T01a_stage_a_triage.json")
    props = schema.get("properties", {})

    st.subheader("Stage A — Triage form (T01a)")
    payload: dict[str, Any] = {}
    payload["provider_name"] = st.text_input(
        "Provider name", value=defaults.get("provider_name", ""),
        help="Legal name of the AI system provider (Art. 11). FLI-E1.")
    payload["system_name"] = st.text_input(
        "System name", value=defaults.get("system_name", ""),
        help="Commercial or internal name of the AI system.")
    payload["version"] = st.text_input(
        "Version", value=defaults.get("version", "0.1.0"))
    payload["intended_purpose"] = st.text_area(
        "Intended purpose", value=defaults.get("intended_purpose", ""),
        help="As described by the provider (Art. 13 §3). Material changes "
             "to this can flip a downstream entity into a Provider under "
             "Art. 25 §§1–2 — see FLI-E2.")

    payload["declared_modality"] = st.selectbox(
        "Declared modality",
        options=props.get("declared_modality", {}).get(
            "enum", ["tabular", "nlp", "vision", "audio", "llm", "agentic", "gpai"]),
        index=0,
    )
    payload["declared_risk_tier"] = st.selectbox(
        "Declared risk tier",
        options=props.get("declared_risk_tier", {}).get(
            "enum", ["prohibited", "high", "limited", "minimal", "gpai"]),
        index=1,
        help="Per Art. 6 / Annex III. FLI-HR3/HR4 decide this from the "
             "Annex I/III categories below.",
    )
    payload["declared_annex_iii_sections"] = st.multiselect(
        "Declared Annex III sections",
        options=[str(i) for i in range(1, 9)],
        default=defaults.get("declared_annex_iii_sections", ["5"]),
        help="Annex III high-risk categories (Art. 6 §2). Matches FLI-HR4. "
             "1=Biometrics, 2=Critical infrastructure, 3=Education, "
             "4=Employment, 5=Essential services, 6=Law enforcement, "
             "7=Migration, 8=Justice & democracy.",
    )
    payload["deployment_context"] = st.selectbox(
        "Deployment context",
        options=props.get("deployment_context", {}).get(
            "enum", ["b2b", "b2c", "internal", "public_sector"]),
        index=0,
    )
    payload["provider_elects_third_party"] = st.checkbox(
        "Provider elects third-party conformity assessment",
        value=defaults.get("provider_elects_third_party", False),
        help="Voluntary election under Art. 43 §1(b). Distinct from "
             "third_party_ca_legally_required (FLI-HR3) in the FLI section.")
    payload["gdpr_overlap"] = st.checkbox(
        "GDPR overlap", value=defaults.get("gdpr_overlap", False),
        help="System processes personal data subject to GDPR.")
    payload["gpai_general_purpose"] = st.checkbox(
        "GPAI general purpose", value=defaults.get("gpai_general_purpose", False),
        help="General-Purpose AI model (Arts. 51–55). FLI-R1.")
    payload["special_category_data"] = st.checkbox(
        "Special category data", value=defaults.get("special_category_data", False),
        help="Art. 10 §5 / GDPR Art. 9 special-category data.")

    # Optional fields
    payload["cgsa_assessment_id"] = st.text_input(
        "CGSA assessment id (optional)",
        value=defaults.get("cgsa_assessment_id") or "")
    payload["art43_preview"] = None

    # ── FLI pre-intake scoping fields (collapsed by default) ────────────────
    _render_fli_section(payload, defaults)
    return payload


def _render_fli_section(payload: dict, defaults: dict) -> None:
    """Render the optional FLI-derived scoping fields in an expander.

    All fields are optional and write into the same T01a payload dict.
    The expander label links the reviewer to the source questionnaire.
    """
    with st.expander(
        "Pre-intake scope questions (FLI EU AI Act Compliance Checker)",
        expanded=False,
    ):
        st.caption(
            f"Source: [Future of Life Institute — EU AI Act Compliance Checker]({_FLI_REF}). "
            "All fields below are optional; populate them to enable the scope-gate banner."
        )
        payload["entity_type"] = st.multiselect(
            "FLI-E1 · Entity type(s) under Art. 3 §§2–8",
            options=["provider", "deployer", "distributor", "importer",
                     "product_manufacturer", "authorised_representative"],
            default=defaults.get("entity_type", []),
            help="Recital 83: multiple roles allowed. Drives Art. 16/22/23/24/26/54 routing.",
        )
        payload["art25_status_change"] = st.multiselect(
            "FLI-E2 · Art. 25 §§1–2 modifications (flips you into a Provider)",
            options=["name_trademark", "intended_purpose_change",
                     "substantial_modification", "none"],
            default=defaults.get("art25_status_change", []),
        )
        payload["annex_i_section_b"] = st.multiselect(
            "FLI-HR1 · Annex I Section B sectoral categories",
            options=["civil_aviation_security", "two_three_wheel_vehicles",
                     "agricultural_forestry_vehicles", "marine_equipment",
                     "rail_interoperability", "motor_vehicles", "civil_aviation"],
            default=defaults.get("annex_i_section_b", []),
        )
        payload["annex_i_section_a"] = st.multiselect(
            "FLI-HR2/HR6 · Annex I Section A product categories",
            options=["machinery", "toys", "recreational_craft", "lifts",
                     "atex_equipment", "radio_equipment", "pressure_equipment",
                     "cableway", "ppe", "gas_appliances", "medical_devices",
                     "ivd_medical_devices"],
            default=defaults.get("annex_i_section_a", []),
            help="Used when the AI system is a 'safety component' of a regulated product.",
        )
        payload["third_party_ca_legally_required"] = st.checkbox(
            "FLI-HR3 · Third-party conformity assessment legally required",
            value=defaults.get("third_party_ca_legally_required", False),
            help="Distinct from provider_elects_third_party — this is a legal obligation.",
        )
        payload["art6_derogation_claimed"] = st.checkbox(
            "FLI-HR5 · Art. 6 §3 derogation claimed (no significant risk of harm)",
            value=defaults.get("art6_derogation_claimed", False),
        )
        payload["art6_derogation_rationale"] = st.text_area(
            "FLI-HR5 · Art. 6 §3 derogation rationale (required if claimed)",
            value=defaults.get("art6_derogation_rationale") or "",
        ) or None
        payload["territorial_scope"] = st.multiselect(
            "FLI-S1 · Territorial nexus to the Union (Art. 2)",
            options=["placed_on_eu_market", "gpai_placed_on_eu_market",
                     "established_in_eu", "importer_in_eu",
                     "output_used_in_eu", "none"],
            default=defaults.get("territorial_scope", []),
        )
        payload["gpai_systemic_risk"] = st.checkbox(
            "FLI-R1 · GPAI meets Art. 51 §2 systemic-risk threshold (>10^25 FLOPs)",
            value=defaults.get("gpai_systemic_risk", False),
        )
        payload["art2_exclusion"] = st.selectbox(
            "FLI-R2 · Art. 2 exclusion category (if any)",
            options=["", "military", "third_country_law_enforcement",
                     "research_and_development", "open_source",
                     "personal_use", "none"],
            index=0,
        ) or None
        payload["art5_prohibited_practices"] = st.multiselect(
            "FLI-R3 · Art. 5 prohibited practices (any selection halts engagement)",
            options=["subliminal_manipulation", "exploit_vulnerabilities",
                     "biometric_categorisation", "social_scoring",
                     "predictive_policing", "facial_recognition_db_scraping",
                     "emotion_recognition_workplace_education",
                     "real_time_remote_biometrics", "none"],
            default=defaults.get("art5_prohibited_practices", []),
        )
        payload["art50_transparency_triggers"] = st.multiselect(
            "FLI-R4 · Art. 50 transparency triggers",
            options=["deepfake_content", "public_interest_text",
                     "emotion_or_biometric_categorisation",
                     "direct_interaction_with_persons",
                     "synthetic_content_generation", "none"],
            default=defaults.get("art50_transparency_triggers", []),
        )
        payload["is_public_body_or_public_service"] = st.checkbox(
            "FLI-R5 · Public-law body or private entity providing public services",
            value=defaults.get("is_public_body_or_public_service", False),
            help="Combined with risk_tier=high this triggers an Art. 27 FRIA obligation.",
        )


# ---------------------------------------------------------------------------
# Stage B form (URIs only — full schema editing is out of scope for the demo)
# ---------------------------------------------------------------------------

def _render_stage_b(defaults: dict) -> dict:
    """Render minimal Stage B (T01b) form for the demo."""
    st.subheader("Stage B — Annex IV dossier (T01b, summary view)")
    st.caption("Demo loads a fixture; editing dossier sections is out of scope.")
    raw = st.text_area(
        "Annex IV dossier JSON",
        value=json.dumps(defaults or _load_fixture("stage_b.json"), indent=2),
        height=300,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        st.error(f"Stage B JSON parse error: {exc}")
        return defaults or {}


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

async def _run_pipeline(
    engagement_id: str,
    stage_a: dict,
    stage_b: dict,
    stage_c: dict | None,
) -> tuple[dict, EvidenceStore]:
    store = EvidenceStore()
    stage_a_uri = store.store_artefact(
        engagement_id, "stage_a_raw", "stage_a_raw", stage_a, "streamlit")
    stage_b_uri = store.store_artefact(
        engagement_id, "stage_b_raw", "stage_b_raw", stage_b, "streamlit")
    stage_c_uri = (
        store.store_artefact(
            engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "streamlit")
        if stage_c is not None else None
    )
    dispatch: IntakeDispatch = {
        "engagement_id": engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }
    intake = IntakeValidator(evidence_store=store)
    initial = await intake.process(dispatch)
    orch = Orchestrator(evidence_store=store)
    final = await orch.run(dict(initial))
    return final, store


def _live_completeness(stage_a: dict, stage_b: dict) -> float | None:
    """Compute KPI 0 preview from the in-flight Stage A/B payloads."""
    try:
        submission = {
            "stage_a": stage_a, "stage_b": stage_b,
            "stage_c": None, "intake_completeness_score": 0.0,
        }
        rep = intake_completeness_calculator(
            submission=submission,
            declared_modality=stage_a.get("declared_modality", "tabular"),
            engagement_id="preview",
        )
        return float(rep.score)
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="AAA Demo", layout="wide")
    st.title("AAA — Autonomous AI Auditor (Demo)")

    engagement_id = st.text_input(
        "Engagement ID", value="eng-uci-german-credit-001")

    col_a, col_b = st.columns(2)
    with col_a:
        stage_a = _render_stage_a(_load_fixture("stage_a.json"))
    with col_b:
        stage_b = _render_stage_b(_load_fixture("stage_b.json"))

    stage_c = _load_fixture("stage_c.json") or None

    # Live scope-gate banner (FLI-derived pre-intake check)
    gate = scope_gate(stage_a)
    if gate.verdict == "prohibited":
        st.error(f"⛔ Scope gate: **prohibited** — {gate.reasoning[0]}")
    elif gate.verdict == "excluded":
        st.warning(f"⚠ Scope gate: **excluded** — {gate.reasoning[0]}")
    elif gate.verdict == "out_of_scope":
        st.warning(f"⚠ Scope gate: **out of scope** — {gate.reasoning[0]}")
    else:
        st.info("✅ Scope gate: **in scope** — " + " | ".join(gate.reasoning))

    # Live KPI 0 preview
    score = _live_completeness(stage_a, stage_b)
    if score is not None:
        st.metric("Live intake_completeness_score (gate ≥ 0.80)", f"{score:.2f}")
        st.progress(min(max(score, 0.0), 1.0))

    if st.button("Run full audit", type="primary", disabled=gate.halt_engagement):
        with st.spinner("Running IntakeValidator → Orchestrator …"):
            try:
                final, store = asyncio.run(_run_pipeline(
                    engagement_id, stage_a, stage_b, stage_c))
            except IntakeValidatorError as exc:
                st.error(f"IntakeValidator failed at stage {exc.stage}: {exc.reason}")
                return

        st.success(f"Final verdict: **{final.get('final_verdict')}**")
        cols = st.columns(3)
        cols[0].metric("intake_completeness_score",
                       f"{final.get('intake_completeness_score') or 0:.2f}")
        cols[1].metric("completeness_score (KPI 1)",
                       f"{final.get('completeness_score') or 0:.2f}")
        cols[2].metric("regulatory_coverage_pct (KPI 2)",
                       f"{final.get('regulatory_coverage_pct') or 0:.1f}%")

        st.subheader("Compliance matrix")
        st.json(final.get("compliance_matrix", {}))

        st.subheader("Phase artefacts")
        st.json({tid: ref.get("uri") if isinstance(ref, dict) else None
                 for tid, ref in (final.get("phase_artefacts") or {}).items()})

        # Downloads
        summary_bytes = json.dumps(final, indent=2, default=str).encode()
        st.download_button("⬇ Download final AuditState (JSON)",
                           data=summary_bytes,
                           file_name=f"{engagement_id}_audit_state.json",
                           mime="application/json")

        t17 = store.get_artefact(
            (final.get("phase_artefacts") or {})
            .get("T17_compliance_matrix", {}).get("uri", "")) or {}
        t18 = store.get_artefact(
            (final.get("phase_artefacts") or {})
            .get("T18_audit_report", {}).get("uri", "")) or {}
        st.download_button("⬇ Download T17 compliance matrix (JSON)",
                           data=json.dumps(t17, indent=2, default=str).encode(),
                           file_name=f"{engagement_id}_T17.json",
                           mime="application/json")
        st.download_button("⬇ Download T18 audit report (JSON)",
                           data=json.dumps(t18, indent=2, default=str).encode(),
                           file_name=f"{engagement_id}_T18.json",
                           mime="application/json")


if __name__ == "__main__":
    main()
