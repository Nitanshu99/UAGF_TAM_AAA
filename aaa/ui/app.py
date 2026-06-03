"""
aaa.ui.app — EU AI Act Compliance Audit Wizard (§10, §11).

5-step guided workflow:

  0. Start Engagement — provide an ID.
  1. Upload Documents — technical docs, model artefacts, datasets.
  2. Quick Questions — 8 questions the agent cannot answer from documents alone.
  3. Review & Confirm — inspect and edit agent-pre-filled Stage A + Stage B fields.
  4. Results — final verdict, KPI metrics, compliance matrix, downloads.

Run::

    AAA_OFFLINE_MODE=true \\
    CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \\
    streamlit run aaa/ui/app.py
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import uuid
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st  # noqa: E402

from aaa.agents.base import IntakeDispatch  # noqa: E402
from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError  # noqa: E402
from aaa.agents.tier1.orchestrator import Orchestrator  # noqa: E402
from aaa.platform.evidence import EvidenceStore  # noqa: E402
from aaa.tools.intake_completeness_calculator import intake_completeness_calculator  # noqa: E402
from aaa.tools.scope_gate import scope_gate  # noqa: E402

_TEMPLATES_DIR = REPO_ROOT / "templates"
_FIXTURE_DIR = REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit"

# ---------------------------------------------------------------------------
# Annex III section labels (plain English for the questionnaire)
# ---------------------------------------------------------------------------
_ANNEX_III_LABELS: dict[str, str] = {
    "1": "1 — Biometric identification and categorisation of natural persons",
    "2": "2 — Management and operation of critical infrastructure",
    "3": "3 — Education and vocational training",
    "4": "4 — Employment, worker management and access to self-employment",
    "5": "5 — Access to and enjoyment of essential private/public services (e.g. credit, insurance)",
    "6": "6 — Law enforcement",
    "7": "7 — Migration, asylum and border control",
    "8": "8 — Administration of justice and democratic processes",
}

# Supporting document upload fields: field_key → (label, description, allowed_types)
_DOC_UPLOAD_FIELDS: dict[str, tuple[str, str, list[str]]] = {
    "risk_management_file_uri": (
        "Risk management documentation",
        "§5 / Art. 9 — Your risk management system file",
        ["pdf", "doc", "docx"],
    ),
    "eu_doc_uri": (
        "EU Declaration of Conformity",
        "§8 — Signed declaration of conformity (if available)",
        ["pdf", "doc", "docx"],
    ),
    "post_market_plan_uri": (
        "Post-market monitoring plan",
        "§9 / Art. 72 — Your post-deployment monitoring plan",
        ["pdf", "doc", "docx"],
    ),
    "system_prompt_uri": (
        "System prompt",
        "LLM / Agentic only — The system prompt used by the model",
        ["txt", "md", "json"],
    ),
    "rag_manifest_uri": (
        "RAG manifest",
        "LLM / Agentic only — Vector-store schema and retrieval configuration",
        ["json", "yaml", "yml"],
    ),
    "guardrail_config_uri": (
        "Guardrail configuration",
        "LLM / Agentic only — Content-filter or safety guardrail configuration",
        ["json", "yaml", "yml"],
    ),
    "golden_set_uri": (
        "Golden evaluation set",
        "LLM / Agentic only — At least 50 Q&A pairs for evaluation",
        ["json", "csv"],
    ),
}

_OPTIONAL_UPLOAD_FIELDS: dict[str, tuple[str, str, list[str]]] = {
    "training_dataset_uri": (
        "Training dataset",
        "Optional — The dataset used to train the model",
        ["csv", "parquet", "json"],
    ),
    "evaluation_dataset_uri": (
        "Evaluation dataset",
        "Optional — The dataset used to evaluate/test the model",
        ["csv", "parquet", "json"],
    ),
    "model_artifact_uri": (
        "Model artefact",
        "Optional — The trained model file",
        ["pkl", "joblib", "onnx", "pt", "safetensors", "zip"],
    ),
    "model_metadata_uri": (
        "Model metadata",
        "Optional — Model card or metadata file",
        ["json", "md", "txt"],
    ),
}


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _load_schema(name: str) -> dict:
    return json.loads((_TEMPLATES_DIR / name).read_text())


@st.cache_data(show_spinner=False)
def _load_fixture(name: str) -> dict:
    path = _FIXTURE_DIR / name
    return json.loads(path.read_text()) if path.exists() else {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _store_uploaded_file(
    store: EvidenceStore,
    engagement_id: str,
    role: str,
    uploaded: Any,
) -> str | None:
    if uploaded is None:
        return None
    return store.store_file(
        engagement_id=engagement_id,
        phase="customer_uploads",
        artefact_type=role,
        filename=uploaded.name,
        content_type=getattr(uploaded, "type", None) or "application/octet-stream",
        data=uploaded.getvalue(),
        agent_name="streamlit",
    )


def _init_key(key: str, default: Any) -> None:
    """Set session state key only on first call — never overwrites a user edit."""
    if key not in st.session_state:
        st.session_state[key] = default


def _confidence_label(score: float) -> str:
    if score >= 0.7:
        return "high confidence"
    if score >= 0.4:
        return "medium confidence"
    return "low confidence"


# ---------------------------------------------------------------------------
# Async pipeline wrappers
# ---------------------------------------------------------------------------

async def _run_extraction(
    engagement_id: str,
    doc_uris: list[str],
    store: EvidenceStore,
) -> dict:
    from aaa.agents.doc_intelligence import DocIntelligenceAgent
    agent = DocIntelligenceAgent(evidence_store=store)
    return await agent.process({"engagement_id": engagement_id, "doc_uris": doc_uris})


async def _run_pipeline(
    engagement_id: str,
    stage_a: dict,
    stage_b: dict,
    stage_c: dict | None,
    store: EvidenceStore,
) -> dict:
    stage_a_uri = store.store_artefact(engagement_id, "stage_a_raw", "stage_a_raw", stage_a, "streamlit")
    stage_b_uri = store.store_artefact(engagement_id, "stage_b_raw", "stage_b_raw", stage_b, "streamlit")
    stage_c_uri = (
        store.store_artefact(engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "streamlit")
        if stage_c is not None else None
    )
    dispatch: IntakeDispatch = {
        "engagement_id": engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }
    initial = await IntakeValidator(evidence_store=store).process(dispatch)
    final = await Orchestrator(evidence_store=store).run(dict(initial))
    return final


def _live_completeness(stage_a: dict, stage_b: dict) -> float | None:
    try:
        rep = intake_completeness_calculator(
            submission={"stage_a": stage_a, "stage_b": stage_b, "stage_c": None, "intake_completeness_score": 0.0},
            declared_modality=stage_a.get("declared_modality", "tabular"),
            engagement_id="preview",
        )
        return float(rep.score)
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Stage A / B payload collectors (read from widget session state keys)
# ---------------------------------------------------------------------------

def _collect_stage_a() -> dict:
    s = st.session_state
    return {
        "provider_name": s.get("s3_a_provider_name", ""),
        "system_name": s.get("s3_a_system_name", ""),
        "version": s.get("s3_a_version", "0.1.0"),
        "intended_purpose": s.get("s3_a_intended_purpose", ""),
        "declared_modality": s.get("s3_a_declared_modality", "tabular"),
        "declared_risk_tier": s.get("s3_a_declared_risk_tier", "limited"),
        "declared_annex_iii_sections": s.get("s3_a_declared_annex_iii_sections", []),
        "deployment_context": s.get("s3_a_deployment_context", "b2b"),
        "provider_elects_third_party": s.get("s3_a_provider_elects_third_party", False),
        "gdpr_overlap": s.get("s3_a_gdpr_overlap", False),
        "gpai_general_purpose": s.get("s3_a_gpai_general_purpose", False),
        "special_category_data": s.get("s3_a_special_category_data", False),
        "art43_preview": None,
        "cgsa_assessment_id": s.get("s3_a_cgsa_assessment_id") or None,
        "entity_type": s.get("s3_a_entity_type", []),
        "territorial_scope": s.get("s3_a_territorial_scope", []),
        "art25_status_change": s.get("s3_a_art25_status_change", []),
        "annex_i_section_a": s.get("s3_a_annex_i_section_a", []),
        "annex_i_section_b": s.get("s3_a_annex_i_section_b", []),
        "third_party_ca_legally_required": s.get("s3_a_third_party_ca_legally_required", False),
        "art6_derogation_claimed": s.get("s3_a_art6_derogation_claimed", False),
        "art6_derogation_rationale": s.get("s3_a_art6_derogation_rationale") or None,
        "gpai_systemic_risk": s.get("s3_a_gpai_systemic_risk", False),
        "art2_exclusion": s.get("s3_a_art2_exclusion") or None,
        "art5_prohibited_practices": s.get("s3_a_art5_prohibited_practices", []),
        "art50_transparency_triggers": s.get("s3_a_art50_transparency_triggers", []),
        "is_public_body_or_public_service": s.get("s3_a_is_public_body_or_public_service", False),
    }


def _collect_stage_b() -> dict:
    s = st.session_state
    raw_metrics = s.get("s3_b_accuracy_metrics_raw", '{"accuracy": 0.8}')
    try:
        accuracy_metrics: Any = json.loads(raw_metrics)
    except json.JSONDecodeError:
        accuracy_metrics = {}
    lifecycle_raw = s.get("s3_b_lifecycle_change_log_raw", "")
    lifecycle = [ln for ln in lifecycle_raw.splitlines() if ln.strip()]
    harmonised = [x.strip() for x in s.get("s3_b_harmonised_standards_raw", "").split(",") if x.strip()]
    other = [x.strip() for x in s.get("s3_b_other_standards_raw", "").split(",") if x.strip()]
    result: dict[str, Any] = {
        "general_description": s.get("s3_b_general_description", ""),
        "model_type": s.get("s3_b_model_type", ""),
        "design_process": s.get("s3_b_design_process", ""),
        "training_data_description": s.get("s3_b_training_data_description", ""),
        "data_governance_measures": s.get("s3_b_data_governance_measures", ""),
        "monitoring_measures": s.get("s3_b_monitoring_measures", ""),
        "logging_capabilities": s.get("s3_b_logging_capabilities", ""),
        "accuracy_metrics": accuracy_metrics,
        "lifecycle_change_log": lifecycle,
        "harmonised_standards": harmonised,
        "other_standards": other,
    }
    for key in {**_DOC_UPLOAD_FIELDS, **_OPTIONAL_UPLOAD_FIELDS}:
        uri = (s.get("s3_b_uris") or {}).get(key)
        if uri:
            result[key] = uri
    return result


# ---------------------------------------------------------------------------
# Step renderers
# ---------------------------------------------------------------------------

def _render_progress(step: int) -> None:
    labels = ["Start", "Upload Documents", "Quick Questions", "Review & Confirm", "Results"]
    cols = st.columns(len(labels))
    for i, (col, label) in enumerate(zip(cols, labels)):
        if i < step:
            col.write(f"✓ {label}")
        elif i == step:
            col.write(f"**› {label}**")
        else:
            col.write(f"· {label}")
    st.divider()


def _render_step_0() -> None:
    st.title("EU AI Act Compliance Audit")
    st.write(
        "This wizard guides you through an autonomous EU AI Act compliance audit of your AI system. "
        "Upload your technical documentation and the auditing agent will read it, "
        "pre-fill the required compliance form, and run a full audit across all relevant EU AI Act articles. "
        "You review and confirm before the audit begins."
    )
    st.write("**What you will need:**")
    st.write(
        "- Technical documentation for your AI system (model card, data sheet, risk assessment, system spec)\n"
        "- Model artefact and/or evaluation datasets (optional but improve audit depth)\n"
        "- About 10 minutes to review the pre-filled form"
    )
    st.divider()
    default_id = f"eng-{uuid.uuid4().hex[:8]}"
    eid = st.text_input(
        "Engagement ID",
        value=st.session_state.get("engagement_id", default_id),
        help="A unique identifier for this audit engagement. Auto-generated — you can change it.",
    )
    if st.button("Start Audit", type="primary"):
        st.session_state["engagement_id"] = eid
        if "aaa_evidence_store" not in st.session_state:
            st.session_state["aaa_evidence_store"] = EvidenceStore()
        st.session_state["step"] = 1
        st.rerun()


def _render_step_1() -> None:
    st.header("Upload Your System Documentation")
    st.write(
        "Upload any documents that describe your AI system. "
        "The agent will read them and pre-fill the compliance form in the next step. "
        "You can always edit or add information manually."
    )

    store: EvidenceStore = st.session_state["aaa_evidence_store"]
    eid: str = st.session_state["engagement_id"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Technical documents")
        st.caption("Model card, technical spec, data sheet, risk assessment, system description, etc.")
        doc_files = st.file_uploader(
            "Upload documents",
            accept_multiple_files=True,
            type=["pdf", "docx", "doc", "txt", "md"],
            key="step1_docs",
            label_visibility="collapsed",
        )
    with col2:
        st.subheader("Model artefact (optional)")
        st.caption("The trained model file — improves technical validation depth.")
        model_file = st.file_uploader(
            "Upload model",
            type=["pkl", "joblib", "onnx", "pt", "safetensors", "zip"],
            key="step1_model",
            label_visibility="collapsed",
        )
        st.subheader("Datasets (optional)")
        st.caption("Training or evaluation dataset files.")
        dataset_files = st.file_uploader(
            "Upload datasets",
            accept_multiple_files=True,
            type=["csv", "parquet", "json"],
            key="step1_datasets",
            label_visibility="collapsed",
        )

    st.divider()
    col_back, col_fwd = st.columns([1, 4])
    with col_back:
        if st.button("← Back"):
            st.session_state["step"] = 0
            st.rerun()
    with col_fwd:
        can_proceed = bool(doc_files or model_file or dataset_files)
        skip_label = "Continue without documents →" if not can_proceed else "Analyse Documents →"
        if st.button(skip_label, type="primary" if can_proceed else "secondary"):
            doc_uris: list[str] = []
            for f in (doc_files or []):
                uri = _store_uploaded_file(store, eid, "technical_doc", f)
                if uri:
                    doc_uris.append(uri)
            if model_file:
                uri = _store_uploaded_file(store, eid, "model_artifact_uri", model_file)
                if uri:
                    doc_uris.append(uri)
            for f in (dataset_files or []):
                uri = _store_uploaded_file(store, eid, "training_dataset", f)
                if uri:
                    doc_uris.append(uri)
            st.session_state["step1_doc_uris"] = doc_uris

            if doc_uris:
                with st.spinner("Agent is reading your documents and extracting compliance information…"):
                    extraction = asyncio.run(_run_extraction(eid, doc_uris, store))
            else:
                extraction = {
                    "stage_a_partial": {},
                    "stage_b_partial": {},
                    "field_confidence": {},
                    "field_sources": {},
                    "missing_fields": [],
                }
            st.session_state["extraction_result"] = extraction
            st.session_state["step3_initialized"] = False
            st.session_state["step"] = 2
            st.rerun()


def _render_step_2() -> None:
    st.header("8 Quick Questions")
    st.write(
        "These questions cover things the agent cannot reliably determine from documents alone. "
        "They take about 2 minutes to complete."
    )

    extraction = st.session_state.get("extraction_result", {})
    stage_a_pre = extraction.get("stage_a_partial", {})

    annex_iii_options = list(_ANNEX_III_LABELS.values())
    annex_iii_keys = list(_ANNEX_III_LABELS.keys())

    with st.form("step2_questions"):
        st.markdown("**1. What is your role in relation to this AI system?**")
        st.caption("Are you the company that built/trained the model (Provider), or deploying someone else's model (Deployer)?")
        entity_type = st.multiselect(
            "Select all that apply",
            options=["provider", "deployer", "distributor", "importer",
                     "product_manufacturer", "authorised_representative"],
            default=[],
            key="q_entity_type",
        )

        st.markdown("**2. Who are the end users of this system?**")
        st.caption("B2B = sold to businesses, B2C = used by consumers directly, Public Sector = government/public authority, Internal = only within your organisation.")
        deployment_context = st.selectbox(
            "Deployment context",
            options=["b2b", "b2c", "public_sector", "internal"],
            index=0,
            key="q_deployment_context",
            label_visibility="collapsed",
        )

        st.markdown("**3. Does this system process personal data?**")
        st.caption("Does it use or produce data that identifies individuals — names, IDs, locations, behaviour, etc.?")
        gdpr_overlap = st.checkbox("Yes, it processes personal data", key="q_gdpr_overlap")

        if gdpr_overlap:
            st.markdown("**4. Does it process special-category data?**")
            st.caption("Health records, biometrics, political or religious beliefs, racial/ethnic origin — see GDPR Art. 9.")
            special_category_data = st.checkbox("Yes, it processes special-category data", key="q_special_category")
        else:
            special_category_data = False

        st.markdown("**5. Is this a General-Purpose AI (GPAI) model?**")
        st.caption("A foundation model or LLM designed for many different tasks, not one specific use case (Arts. 51–55 EU AI Act).")
        gpai_general_purpose = st.checkbox("Yes, this is a general-purpose AI model", key="q_gpai")

        st.markdown("**6. Does this system fall under any Annex III high-risk categories?**")
        st.caption("Select any categories that apply to your system's use case.")
        annex_iii_selected_labels = st.multiselect(
            "Annex III categories",
            options=annex_iii_options,
            default=[],
            key="q_annex_iii",
            label_visibility="collapsed",
        )

        st.markdown("**7. Are you electing a voluntary third-party conformity assessment?**")
        st.caption("Choose to have a notified body independently verify compliance, even if not legally required (Art. 43 §1(b)).")
        provider_elects_third_party = st.checkbox("Yes, we elect voluntary third-party assessment", key="q_third_party")

        st.markdown("**8. Where is this system placed on the market or used?**")
        st.caption("Select all territories that apply for EU AI Act coverage.")
        territorial_scope = st.multiselect(
            "Territory",
            options=["placed_on_eu_market", "gpai_placed_on_eu_market",
                     "established_in_eu", "importer_in_eu",
                     "output_used_in_eu", "none"],
            default=[],
            key="q_territorial_scope",
            label_visibility="collapsed",
        )

        st.divider()
        col_back, col_fwd = st.columns([1, 4])
        with col_back:
            back = st.form_submit_button("← Back")
        with col_fwd:
            proceed = st.form_submit_button("Continue →", type="primary")

    if back:
        st.session_state["step"] = 1
        st.rerun()

    if proceed:
        annex_iii_sections = [annex_iii_keys[annex_iii_options.index(lbl)] for lbl in annex_iii_selected_labels]
        st.session_state["questionnaire_answers"] = {
            "entity_type": entity_type,
            "deployment_context": deployment_context,
            "gdpr_overlap": gdpr_overlap,
            "special_category_data": special_category_data,
            "gpai_general_purpose": gpai_general_purpose,
            "declared_annex_iii_sections": annex_iii_sections,
            "provider_elects_third_party": provider_elects_third_party,
            "territorial_scope": territorial_scope,
        }
        st.session_state["step3_initialized"] = False
        st.session_state["step"] = 3
        st.rerun()


def _field_caption(field: str, confidence: dict, sources: dict, missing: list) -> None:
    """Show auto-fill provenance or a missing-field warning below a widget."""
    if field in confidence:
        pct = int(confidence[field] * 100)
        src = sources.get(field, "document")
        st.caption(f"Auto-filled from {src} · {pct}% {_confidence_label(confidence[field])}")
    elif field in missing:
        st.warning(f"Not found in uploaded documents — please fill in manually.")


def _render_step_3() -> None:
    store: EvidenceStore = st.session_state["aaa_evidence_store"]
    eid: str = st.session_state["engagement_id"]
    extraction: dict = st.session_state.get("extraction_result", {})
    questionnaire: dict = st.session_state.get("questionnaire_answers", {})
    stage_a_pre: dict = extraction.get("stage_a_partial", {})
    stage_b_pre: dict = extraction.get("stage_b_partial", {})
    confidence: dict = extraction.get("field_confidence", {})
    sources: dict = extraction.get("field_sources", {})
    missing: list = extraction.get("missing_fields", [])

    # Pre-populate widget keys from extraction + questionnaire on first arrival.
    if not st.session_state.get("step3_initialized"):
        _init_key("s3_a_provider_name", stage_a_pre.get("provider_name", ""))
        _init_key("s3_a_system_name", stage_a_pre.get("system_name", ""))
        _init_key("s3_a_version", stage_a_pre.get("version", "0.1.0"))
        _init_key("s3_a_intended_purpose", stage_a_pre.get("intended_purpose", ""))
        _init_key("s3_a_declared_modality", stage_a_pre.get("declared_modality", "tabular"))
        _init_key("s3_a_declared_risk_tier", stage_a_pre.get("declared_risk_tier", "limited"))
        _init_key("s3_a_cgsa_assessment_id", stage_a_pre.get("cgsa_assessment_id", ""))
        # From questionnaire
        _init_key("s3_a_deployment_context", questionnaire.get("deployment_context", "b2b"))
        _init_key("s3_a_gdpr_overlap", questionnaire.get("gdpr_overlap", False))
        _init_key("s3_a_special_category_data", questionnaire.get("special_category_data", False))
        _init_key("s3_a_gpai_general_purpose", questionnaire.get("gpai_general_purpose", False))
        _init_key("s3_a_declared_annex_iii_sections", questionnaire.get("declared_annex_iii_sections", []))
        _init_key("s3_a_provider_elects_third_party", questionnaire.get("provider_elects_third_party", False))
        _init_key("s3_a_entity_type", questionnaire.get("entity_type", []))
        _init_key("s3_a_territorial_scope", questionnaire.get("territorial_scope", []))
        _init_key("s3_a_art25_status_change", [])
        _init_key("s3_a_annex_i_section_a", [])
        _init_key("s3_a_annex_i_section_b", [])
        _init_key("s3_a_third_party_ca_legally_required", False)
        _init_key("s3_a_art6_derogation_claimed", False)
        _init_key("s3_a_art6_derogation_rationale", "")
        _init_key("s3_a_gpai_systemic_risk", False)
        _init_key("s3_a_art2_exclusion", "")
        _init_key("s3_a_art5_prohibited_practices", [])
        _init_key("s3_a_art50_transparency_triggers", [])
        _init_key("s3_a_is_public_body_or_public_service", False)
        # Stage B
        _init_key("s3_b_general_description", stage_b_pre.get("general_description", ""))
        _init_key("s3_b_model_type", stage_b_pre.get("model_type", ""))
        _init_key("s3_b_design_process", stage_b_pre.get("design_process", ""))
        _init_key("s3_b_training_data_description", stage_b_pre.get("training_data_description", ""))
        _init_key("s3_b_data_governance_measures", stage_b_pre.get("data_governance_measures", ""))
        _init_key("s3_b_monitoring_measures", stage_b_pre.get("monitoring_measures", ""))
        _init_key("s3_b_logging_capabilities", stage_b_pre.get("logging_capabilities", ""))
        raw_m = stage_b_pre.get("accuracy_metrics", "")
        _init_key("s3_b_accuracy_metrics_raw",
                  raw_m if isinstance(raw_m, str) else json.dumps(raw_m) if raw_m else '{"accuracy": 0.8}')
        lc = stage_b_pre.get("lifecycle_change_log", "")
        _init_key("s3_b_lifecycle_change_log_raw",
                  lc if isinstance(lc, str) else "\n".join(lc) if isinstance(lc, list) else "")
        hs = stage_b_pre.get("harmonised_standards", "")
        _init_key("s3_b_harmonised_standards_raw",
                  hs if isinstance(hs, str) else ", ".join(hs) if isinstance(hs, list) else "")
        os_ = stage_b_pre.get("other_standards", "")
        _init_key("s3_b_other_standards_raw",
                  os_ if isinstance(os_, str) else ", ".join(os_) if isinstance(os_, list) else "")
        _init_key("s3_b_uris", {})
        st.session_state["step3_initialized"] = True

    # Build current payloads for live completeness score.
    stage_a = _collect_stage_a()
    stage_b = _collect_stage_b()

    # ── Live completeness + scope gate ───────────────────────────────────────
    score = _live_completeness(stage_a, stage_b)
    gate = scope_gate(stage_a)

    col_score, col_gate = st.columns([1, 2])
    with col_score:
        if score is not None:
            st.metric("Intake completeness (gate ≥ 0.80)", f"{score:.0%}")
            st.progress(min(max(score, 0.0), 1.0))
    with col_gate:
        if gate.verdict == "prohibited":
            st.error(f"⛔ Scope gate: prohibited — {gate.reasoning[0]}")
        elif gate.verdict in {"excluded", "out_of_scope"}:
            st.warning(f"⚠ Scope gate: {gate.verdict} — {gate.reasoning[0]}")
        else:
            st.success("✅ Scope gate: in scope")

    st.write(
        "Review the information below. Fields pre-filled by the agent show their "
        "source and confidence. Edit any field — changes update the completeness score live."
    )

    # ── Stage A ───────────────────────────────────────────────────────────────
    schema_props = _load_schema("T01a_stage_a_triage.json").get("properties", {})

    with st.expander("Stage A — System Declaration (T01a)", expanded=True):
        st.markdown("*Core information about your AI system and its regulatory classification.*")

        st.text_input(
            "Legal provider name",
            key="s3_a_provider_name",
            help="Art. 11 — Full legal name of the organisation that developed or places this AI system on the market. E.g. 'Acme Analytics GmbH'",
            placeholder="e.g. Acme Analytics GmbH",
        )
        _field_caption("provider_name", confidence, sources, missing)

        st.text_input(
            "System name",
            key="s3_a_system_name",
            help="Commercial or internal name used to identify this AI system. E.g. 'CreditScoreRef v2'",
            placeholder="e.g. CreditScoreRef v2",
        )
        _field_caption("system_name", confidence, sources, missing)

        st.text_input(
            "Version",
            key="s3_a_version",
            help="Semantic version number (major.minor or major.minor.patch). E.g. '1.0' or '2.3.1'",
            placeholder="e.g. 1.0.0",
        )
        _field_caption("version", confidence, sources, missing)

        st.text_area(
            "Intended purpose",
            key="s3_a_intended_purpose",
            help="Art. 13 — Describe what this system is designed to do, who uses it, and in what context. Minimum 20 characters.",
            placeholder="e.g. Automated credit-scoring for retail banking customers in the EU to support loan eligibility decisions.",
            height=90,
        )
        _field_caption("intended_purpose", confidence, sources, missing)

        modality_opts = schema_props.get("declared_modality", {}).get(
            "enum", ["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"])
        current_modality = st.session_state.get("s3_a_declared_modality", "tabular")
        modality_idx = modality_opts.index(current_modality) if current_modality in modality_opts else 0
        st.selectbox(
            "AI modality",
            options=modality_opts,
            index=modality_idx,
            key="s3_a_declared_modality",
            help=(
                "Primary technical type of this AI system. "
                "tabular = structured data / classical ML, "
                "cv = computer vision, "
                "nlp = text/language processing, "
                "time_series = forecasting, "
                "llm = large language model, "
                "agentic = autonomous agent system, "
                "gpai = general-purpose foundation model."
            ),
        )
        _field_caption("declared_modality", confidence, sources, missing)

        tier_opts = schema_props.get("declared_risk_tier", {}).get(
            "enum", ["high", "limited", "minimal", "gpai"])
        current_tier = st.session_state.get("s3_a_declared_risk_tier", "limited")
        tier_idx = tier_opts.index(current_tier) if current_tier in tier_opts else 0
        st.selectbox(
            "Self-assessed risk tier",
            options=tier_opts,
            index=tier_idx,
            key="s3_a_declared_risk_tier",
            help=(
                "Art. 6 — Your own assessment of the risk tier. "
                "high = Annex III use case (most obligations), "
                "limited = transparency obligations only (Art. 50), "
                "minimal = no specific EU AI Act obligations, "
                "gpai = general-purpose AI model (Arts. 51–55)."
            ),
        )
        _field_caption("declared_risk_tier", confidence, sources, missing)

        st.multiselect(
            "Annex III high-risk categories",
            options=list(_ANNEX_III_LABELS.values()),
            default=[
                _ANNEX_III_LABELS[k]
                for k in st.session_state.get("s3_a_declared_annex_iii_sections", [])
                if k in _ANNEX_III_LABELS
            ],
            key="_s3_annex_iii_labels",
            help=(
                "Art. 6 §2 — Select every Annex III category that applies to your system. "
                "At least one selection triggers high-risk obligations unless Art. 6 §3 derogation applies."
            ),
        )
        # Sync the label selection back to the section-number key.
        annex_iii_keys = list(_ANNEX_III_LABELS.keys())
        annex_iii_vals = list(_ANNEX_III_LABELS.values())
        st.session_state["s3_a_declared_annex_iii_sections"] = [
            annex_iii_keys[annex_iii_vals.index(lbl)]
            for lbl in (st.session_state.get("_s3_annex_iii_labels") or [])
        ]

        st.selectbox(
            "Deployment context",
            options=["b2b", "b2c", "public_sector", "internal"],
            index=["b2b", "b2c", "public_sector", "internal"].index(
                st.session_state.get("s3_a_deployment_context", "b2b")),
            key="s3_a_deployment_context",
            help=(
                "Who uses this system directly? "
                "b2b = sold to/used by other businesses, "
                "b2c = used directly by consumers, "
                "public_sector = government or public authority, "
                "internal = used only within your own organisation."
            ),
        )

        st.checkbox(
            "System processes personal data (GDPR overlap)",
            key="s3_a_gdpr_overlap",
            help="Does the system use or produce data that identifies individuals? Triggers GDPR Art. 35 / DPIA review.",
        )
        st.checkbox(
            "System processes special-category data",
            key="s3_a_special_category_data",
            help="Health records, biometrics, political/religious beliefs, racial/ethnic origin — see GDPR Art. 9 and EU AI Act Art. 10 §5.",
        )
        st.checkbox(
            "This is a General-Purpose AI (GPAI) model",
            key="s3_a_gpai_general_purpose",
            help="A foundation model or LLM designed to handle many different tasks (Arts. 51–55 EU AI Act).",
        )
        st.checkbox(
            "Elect voluntary third-party conformity assessment",
            key="s3_a_provider_elects_third_party",
            help="Art. 43 §1(b) — Choose to have a notified body independently verify compliance even if not legally required.",
        )

        st.text_input(
            "CGSA assessment ID (optional)",
            key="s3_a_cgsa_assessment_id",
            help="If this system was previously assessed under the CGSA / S4 framework, provide the assessment ID here.",
            placeholder="e.g. cgsa-2024-001",
        )

        with st.expander("Advanced compliance fields (FLI EU AI Act Compliance Checker)", expanded=False):
            st.caption(
                "These fields are derived from the Future of Life Institute EU AI Act Compliance Checker. "
                "All are optional — populate them for a more precise scope gate."
            )
            st.multiselect(
                "FLI-E2 · Art. 25 modifications (triggers Provider status)",
                options=["name_trademark", "intended_purpose_change", "substantial_modification", "none"],
                default=st.session_state.get("s3_a_art25_status_change", []),
                key="s3_a_art25_status_change",
            )
            st.multiselect(
                "FLI-HR1 · Annex I Section B sectoral categories",
                options=["civil_aviation_security", "two_three_wheel_vehicles",
                         "agricultural_forestry_vehicles", "marine_equipment",
                         "rail_interoperability", "motor_vehicles", "civil_aviation"],
                default=st.session_state.get("s3_a_annex_i_section_b", []),
                key="s3_a_annex_i_section_b",
            )
            st.multiselect(
                "FLI-HR2 · Annex I Section A product categories",
                options=["machinery", "toys", "recreational_craft", "lifts",
                         "atex_equipment", "radio_equipment", "pressure_equipment",
                         "cableway", "ppe", "gas_appliances", "medical_devices", "ivd_medical_devices"],
                default=st.session_state.get("s3_a_annex_i_section_a", []),
                key="s3_a_annex_i_section_a",
            )
            st.checkbox(
                "FLI-HR3 · Third-party conformity assessment legally required",
                key="s3_a_third_party_ca_legally_required",
            )
            st.checkbox("FLI-HR5 · Art. 6 §3 derogation claimed (no significant risk of harm)",
                        key="s3_a_art6_derogation_claimed")
            if st.session_state.get("s3_a_art6_derogation_claimed"):
                st.text_area("Art. 6 §3 derogation rationale", key="s3_a_art6_derogation_rationale", height=70)
            st.checkbox("FLI-R1 · GPAI meets Art. 51 §2 systemic-risk threshold (>10^25 FLOPs)",
                        key="s3_a_gpai_systemic_risk")
            st.selectbox(
                "FLI-R2 · Art. 2 exclusion category (if any)",
                options=["", "military", "third_country_law_enforcement",
                         "research_and_development", "open_source", "personal_use", "none"],
                index=0,
                key="s3_a_art2_exclusion",
            )
            st.multiselect(
                "FLI-R3 · Art. 5 prohibited practices (any selection halts engagement)",
                options=["subliminal_manipulation", "exploit_vulnerabilities",
                         "biometric_categorisation", "social_scoring",
                         "predictive_policing", "facial_recognition_db_scraping",
                         "emotion_recognition_workplace_education",
                         "real_time_remote_biometrics", "none"],
                default=st.session_state.get("s3_a_art5_prohibited_practices", []),
                key="s3_a_art5_prohibited_practices",
            )
            st.multiselect(
                "FLI-R4 · Art. 50 transparency triggers",
                options=["deepfake_content", "public_interest_text",
                         "emotion_or_biometric_categorisation",
                         "direct_interaction_with_persons",
                         "synthetic_content_generation", "none"],
                default=st.session_state.get("s3_a_art50_transparency_triggers", []),
                key="s3_a_art50_transparency_triggers",
            )
            st.checkbox(
                "FLI-R5 · Public-law body or private entity providing public services",
                key="s3_a_is_public_body_or_public_service",
                help="Triggers Art. 27 Fundamental Rights Impact Assessment when combined with high risk.",
            )

    # ── Stage B ───────────────────────────────────────────────────────────────
    with st.expander("Stage B — Technical Documentation (T01b / Annex IV)", expanded=True):
        st.markdown("*Technical details required under Annex IV §1–§9 of the EU AI Act.*")

        st.text_area(
            "General system description",
            key="s3_b_general_description",
            help="Annex IV §1 — Overall purpose, the problem it solves, who is responsible, and who uses it. Minimum 50 characters.",
            placeholder="e.g. CreditScoreRef is an XGBoost-based credit-risk classifier deployed by Acme Analytics for retail banking partners...",
            height=100,
        )
        _field_caption("general_description", confidence, sources, missing)

        st.text_input(
            "Model architecture / type",
            key="s3_b_model_type",
            help="Annex IV §1 — Technical type and version. E.g. 'XGBoost classifier v1.2', 'BERT fine-tune', 'GPT-4 fine-tune on claims data'.",
            placeholder="e.g. XGBoost classifier v1.2",
        )
        _field_caption("model_type", confidence, sources, missing)

        st.text_area(
            "Design and development process",
            key="s3_b_design_process",
            help="Annex IV §2 — How was the model designed and trained? Include training methodology, architecture choices, key iterations. Minimum 30 characters.",
            placeholder="e.g. Trained on 3 years of anonymised loan application data using 5-fold cross-validation...",
            height=90,
        )
        _field_caption("design_process", confidence, sources, missing)

        st.text_area(
            "Training data description",
            key="s3_b_training_data_description",
            help="Annex IV §2 / Art. 10 — What datasets were used for training and validation? Include source, size, date range, and how data was collected. Minimum 30 characters.",
            placeholder="e.g. 120,000 anonymised retail loan applications from 2020–2023, sourced from internal CRM...",
            height=90,
        )
        _field_caption("training_data_description", confidence, sources, missing)

        st.text_area(
            "Data governance measures",
            key="s3_b_data_governance_measures",
            help="Annex IV §2 — Processes governing data quality, access control, and handling (e.g. anonymisation, consent, bias review). Minimum 20 characters.",
            placeholder="e.g. All data anonymised at source, GDPR DPA executed with data owner, quarterly bias review...",
            height=90,
        )
        _field_caption("data_governance_measures", confidence, sources, missing)

        st.text_area(
            "Monitoring and control measures",
            key="s3_b_monitoring_measures",
            help="Annex IV §3 — How is the system monitored post-deployment? Include drift detection, human oversight triggers, and incident response. Minimum 20 characters.",
            placeholder="e.g. Monthly PSI drift monitoring, human review triggered when PSI > 0.2, incident log reviewed quarterly...",
            height=90,
        )
        _field_caption("monitoring_measures", confidence, sources, missing)

        st.text_area(
            "Logging capabilities",
            key="s3_b_logging_capabilities",
            help="Annex IV §3 / Art. 12 — What logs does the system produce? Include what events are recorded and the retention period. Minimum 10 characters.",
            placeholder="e.g. All predictions logged with input features (anonymised), output score, and timestamp. Logs retained 5 years.",
            height=70,
        )
        _field_caption("logging_capabilities", confidence, sources, missing)

        st.text_area(
            "Performance metrics (JSON)",
            key="s3_b_accuracy_metrics_raw",
            help='Annex IV §4 — Key performance metrics as a JSON object. E.g. {"accuracy": 0.78, "auc": 0.82, "f1": 0.71}. Must be valid JSON.',
            placeholder='{"accuracy": 0.78, "auc": 0.82, "f1": 0.71}',
            height=70,
        )
        _field_caption("accuracy_metrics", confidence, sources, missing)
        try:
            json.loads(st.session_state.get("s3_b_accuracy_metrics_raw", "{}"))
        except json.JSONDecodeError:
            st.error("Performance metrics must be valid JSON.")

        st.text_area(
            "Significant changes log (one change per line)",
            key="s3_b_lifecycle_change_log_raw",
            help="Annex IV §6 — Significant changes since initial deployment, one per line. E.g. 'v1.1 — Retrained on 2024 data to reduce demographic bias'.",
            placeholder="v1.1 — Retrained on 2024 data\nv1.2 — Threshold adjusted for fairness",
            height=70,
        )

        st.text_input(
            "Harmonised standards applied (comma-separated)",
            key="s3_b_harmonised_standards_raw",
            help="Annex IV §7 — ISO, IEC, or EU harmonised standards. E.g. 'ISO/IEC 42001:2023, ISO/IEC 23894:2023'.",
            placeholder="ISO/IEC 42001:2023, ISO/IEC 23894:2023",
        )
        _field_caption("harmonised_standards", confidence, sources, missing)

        st.text_input(
            "Other standards applied (comma-separated)",
            key="s3_b_other_standards_raw",
            help="Annex IV §7 — Other technical or sector-specific standards applied.",
            placeholder="e.g. EBA/GL/2020/06, ISO 31000:2018",
        )

        st.markdown("#### Supporting documents")
        st.caption("Upload the documents listed below. Each has a specific §/Article mapping under Annex IV.")
        for key, (label, description, file_types) in _DOC_UPLOAD_FIELDS.items():
            uploaded = st.file_uploader(f"{label}", type=file_types, key=f"s3_upload_{key}",
                                        help=description)
            if uploaded:
                uri = _store_uploaded_file(store, eid, key, uploaded)
                if uri:
                    st.session_state.setdefault("s3_b_uris", {})[key] = uri
                    st.caption(f"Uploaded: {uploaded.name}")
            elif (st.session_state.get("s3_b_uris") or {}).get(key):
                st.caption("File previously uploaded.")

        st.markdown("#### Model and dataset artefacts (optional)")
        for key, (label, description, file_types) in _OPTIONAL_UPLOAD_FIELDS.items():
            uploaded = st.file_uploader(f"{label}", type=file_types, key=f"s3_upload_{key}",
                                        help=description)
            if uploaded:
                uri = _store_uploaded_file(store, eid, key, uploaded)
                if uri:
                    st.session_state.setdefault("s3_b_uris", {})[key] = uri
                    st.caption(f"Uploaded: {uploaded.name}")

        uploaded_count = len(st.session_state.get("s3_b_uris") or {})
        total_fields = len(_DOC_UPLOAD_FIELDS) + len(_OPTIONAL_UPLOAD_FIELDS)
        st.caption(f"Uploaded/populated URI fields: {uploaded_count} / {total_fields}")

    # ── Navigation ────────────────────────────────────────────────────────────
    st.divider()
    col_back, col_fwd = st.columns([1, 4])
    with col_back:
        if st.button("← Back"):
            st.session_state["step"] = 2
            st.rerun()
    with col_fwd:
        run_disabled = gate.halt_engagement or (score is not None and score < 0.80)
        if run_disabled and score is not None and score < 0.80:
            st.info(f"Intake completeness is {score:.0%} — fill in more fields to reach the 0.80 gate before running.")
        if st.button("Confirm & Run Audit →", type="primary", disabled=run_disabled):
            st.session_state["step4_stage_a"] = _collect_stage_a()
            st.session_state["step4_stage_b"] = _collect_stage_b()
            st.session_state["step"] = 4
            st.rerun()


def _render_step_4() -> None:
    store: EvidenceStore = st.session_state["aaa_evidence_store"]
    eid: str = st.session_state["engagement_id"]
    stage_a: dict = st.session_state["step4_stage_a"]
    stage_b: dict = st.session_state["step4_stage_b"]
    stage_c: dict | None = _load_fixture("stage_c.json") or None

    if "audit_result" not in st.session_state:
        with st.spinner("Running IntakeValidator → Orchestrator (this may take a few minutes)…"):
            try:
                final = asyncio.run(_run_pipeline(eid, stage_a, stage_b, stage_c, store))
                st.session_state["audit_result"] = final
                st.session_state["audit_store"] = store
            except IntakeValidatorError as exc:
                st.error(f"Intake validation failed at stage {exc.stage}: {exc.reason}")
                if st.button("← Back to Review"):
                    st.session_state["step"] = 3
                    st.rerun()
                return

    final: dict = st.session_state["audit_result"]
    store = st.session_state.get("audit_store", store)

    verdict = final.get("final_verdict", "UNKNOWN")
    if verdict == "PASS":
        st.success(f"Final verdict: **{verdict}**")
    elif verdict == "PASS_WITH_OBSERVATIONS":
        st.warning(f"Final verdict: **{verdict}**")
    else:
        st.error(f"Final verdict: **{verdict}**")

    cols = st.columns(3)
    cols[0].metric("Intake completeness (KPI 0)",
                   f"{final.get('intake_completeness_score') or 0:.2f}")
    cols[1].metric("Evidence completeness (KPI 1)",
                   f"{final.get('completeness_score') or 0:.2f}")
    cols[2].metric("Regulatory coverage (KPI 2)",
                   f"{final.get('regulatory_coverage_pct') or 0:.1f}%")

    blocking = final.get("blocking_findings") or []
    if blocking:
        with st.expander(f"Remediation checklist ({len(blocking)} blocking findings)", expanded=True):
            for i, finding in enumerate(blocking, 1):
                st.write(
                    f"**{i}. {finding.get('article', 'Unknown article')}** — "
                    f"{finding.get('description', 'See full report for details')} "
                    f"*(severity: {finding.get('severity', 'unknown')})*"
                )

    st.subheader("Compliance matrix")
    st.json(final.get("compliance_matrix", {}))

    st.subheader("Phase artefacts")
    st.json({tid: ref.get("uri") if isinstance(ref, dict) else None
             for tid, ref in (final.get("phase_artefacts") or {}).items()})

    t17 = store.get_artefact(
        (final.get("phase_artefacts") or {}).get("T17_compliance_matrix", {}).get("uri", "")) or {}
    t18 = store.get_artefact(
        (final.get("phase_artefacts") or {}).get("T18_audit_report", {}).get("uri", "")) or {}
    rendered = t18.get("rendered_report", {}) or {}
    pdf_payload = store.get_artefact(rendered.get("pdf_uri", "")) or {}
    if pdf_payload.get("encoding") == "latin-1":
        st.download_button(
            "⬇ Download audit report (PDF)",
            data=str(pdf_payload.get("body", "")).encode("latin-1"),
            file_name=f"{eid}_audit_report.pdf",
            mime="application/pdf",
        )
    json_payload = store.get_artefact(rendered.get("json_uri", "")) or t18
    st.download_button("⬇ Download T18 audit report (JSON)",
                       data=json.dumps(json_payload, indent=2, default=str).encode(),
                       file_name=f"{eid}_T18.json",
                       mime="application/json")
    st.download_button("⬇ Download T17 compliance matrix (JSON)",
                       data=json.dumps(t17, indent=2, default=str).encode(),
                       file_name=f"{eid}_T17.json",
                       mime="application/json")
    with st.expander("Advanced / debug downloads", expanded=False):
        st.download_button("⬇ Download full AuditState (JSON)",
                           data=json.dumps(final, indent=2, default=str).encode(),
                           file_name=f"{eid}_audit_state.json",
                           mime="application/json")

    if st.button("Start a new audit"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="EU AI Act Compliance Audit", layout="wide")
    if "step" not in st.session_state:
        st.session_state["step"] = 0

    step = st.session_state["step"]
    _render_progress(step)

    if step == 0:
        _render_step_0()
    elif step == 1:
        _render_step_1()
    elif step == 2:
        _render_step_2()
    elif step == 3:
        _render_step_3()
    elif step == 4:
        _render_step_4()


if __name__ == "__main__":
    main()
