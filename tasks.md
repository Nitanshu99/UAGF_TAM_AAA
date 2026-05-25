# AAA — Autonomous AI Auditor: Tasks

> **How to resume in a new conversation:**
> 1. Read `ARCHITECTURE.md` (authoritative design — 1511 lines).
> 2. Find the first group marked **`[ NEXT ]`** below and start there.
> 3. Every group has a **Current state** block listing exactly which files exist, what is missing, and what the group depends on from prior groups — no prior chat context needed.
> 4. After finishing a group, update this file: flip its status to `✅ COMPLETE`, fill in "What was built" and "Key decisions", move `[ NEXT ]` to the following group.
> 5. Just do 1 Group at Once. After finishing 1 group, Ask for explicit user perission to proceed to next group.

---

## ✅ Group 1: Project Initialization and Infrastructure Setup — COMPLETE

**Current state:** All files present on disk. No IDE diagnostics. Safe to import.

### Files created
| File | Purpose |
|------|---------|
| `aaa/__init__.py` and all package `__init__.py` files | Module resolution for `aaa.*` imports |
| `aaa/platform/state.py` | `AuditState` TypedDict + all nested types (§5.1, §5.4) |
| `aaa/agents/base.py` | `BaseAgent` ABC + `IntakeDispatch`, `Dispatch`, `Report`, `Critique` message types (§5.3) |
| `aaa/platform/evidence.py` | `EvidenceStore` — in-memory mock, MinIO-compatible interface (§5.2) |
| `aaa/agents/tier1/regulatory_rag.py` | Placeholder `RegulatoryRAG(BaseAgent)` — to be fleshed out in Group 3 (§3.1 #3) |

### What was built
- **`aaa/platform/state.py`** — All TypedDicts: `StageATriage`, `AnnexIVDossier`, `StageCAccess`, `ClientSubmission`, `AnnexIIIEntry`, `Art43Decision`, `ArtefactRef`, `CGSAPayload`, `CGSAMetadata`, `CGSAOverallScores`, `CGSAAAPhase5Handoff`, `BlockingFinding`, `PositiveFinding`, `LowConfidenceControl`, `FollowUpItem`, `RemediationItem`, `Finding`. Every CGSA/S4 hand-off field from §5.4 is a typed key on `AuditState`.
- **`aaa/agents/base.py`** — `BaseAgent` abstract class; four inter-agent message TypedDicts covering the full `Dispatch → Report → Critique` cycle.
- **`aaa/platform/evidence.py`** — `store_artefact(engagement_id, phase, artefact_type, content, agent_name) → uri` and `get_artefact(uri)`. SHA-256 computed on every write.
- **`aaa/agents/tier1/regulatory_rag.py`** — stub `process(query)` and `search(query)` methods; returns hard-coded strings. Real RAG wired in Group 3.

### Key design decisions
- `AuditState` uses `Optional[X]` everywhere (not `X | None`) for Python 3.9 compatibility via `from __future__ import annotations`.
- `EvidenceStore` is purposefully swappable: swap the constructor to point at real MinIO + Postgres without touching any agent code.

---

## ✅ Group 2: Stage 0 — Intake System — COMPLETE

**Current state:** All files present on disk. Smoke-tested end-to-end (exit 0). No IDE diagnostics.

### Files created
| File | Purpose |
|------|---------|
| `templates/T01a_stage_a_triage.json` | JSON Schema (draft-07) — Stage A ~20-question triage form |
| `templates/T01b_annex_iv_dossier.json` | JSON Schema — Annex IV §1–§9 technical documentation |
| `templates/T01c_intake_completeness_report.json` | JSON Schema — per-section completeness report + gate status |
| `aaa/tools/triage_render.py` | Validates T01a payload; annotates with human-readable labels |
| `aaa/tools/annex_iv_validator.py` | Validates T01b payload; enforces L-branch conditional fields |
| `aaa/tools/intake_completeness_calculator.py` | Computes KPI 0 (`intake_completeness_score`) with §9.1 weights |
| `aaa/tools/art43_select.py` | Deterministic Art. 43 procedure selector — preview + final modes |
| `aaa/agents/intake_validator.py` | `IntakeValidator(BaseAgent)` — Stage 0 A/B/C workflow |

### What was built
- **T01a schema** — required fields: `provider_name`, `system_name`, `version`, `intended_purpose`, `declared_modality`, `declared_risk_tier`, `declared_annex_iii_sections`, `deployment_context`, `provider_elects_third_party`, `gdpr_overlap`, `gpai_general_purpose`, `special_category_data`. Optional: `art43_preview`, `cgsa_assessment_id`, `deployer_name`.
- **T01b schema** — required §1–§7 fields; optional §8–§9 and L-branch fields (`system_prompt_uri`, `rag_manifest_uri`, `tool_inventory`, `guardrail_config_uri`, `golden_set_uri`).
- **T01c schema** — `intake_completeness_score` (0.0–1.0), `section_scores` (§1–§9 each with `score`/`weight`/`label`), `missing_required_fields`, `missing_conditional_fields`, `gate_passed`, Art. 43 delta fields, optional `hitl_threshold_override`.
- **`triage_render`** — validates against T01a schema, adds `is_l_branch`, `triggers_privacy_tier3`, `triggers_gpai_module`, Annex III human labels, `schema_version`.
- **`annex_iv_validator`** — draft-07 JSON Schema check + conditional field enforcement; returns `ValidationResult(is_valid, schema_errors, missing_required, missing_conditional)`.
- **`intake_completeness_calculator`** — section weights `{1:0.20, 2:0.15, 3:0.10, 4:0.15, 5:0.15, 6:0.05, 7:0.10, 8:0.05, 9:0.05}`, gate = 0.80, L-branch missing conditional reduces score by 0.02/field; returns `CompletenessReport`.
- **`art43_select`** — 5-rule decision tree (see §3.5); `Art43SelectInput` dataclass; `art43_select_from_state(state, use_declared=True/False)` convenience wrapper.
- **`IntakeValidator`** — runs: `triage_render` → `art43_select` preview → `annex_iv_validator` → `intake_completeness_calculator` → gate (0.80) → Stage C store → returns populated `AuditState`. Raises `IntakeValidatorError(stage, reason, details)` on any failure.

### Key design decisions
- `art43_select` runs **twice**: preview (Stage A, declared values) → final (after Phase 1, verified values). Delta written to T01c and triggers HITL (§8.4).
- Both `annex_iv_validator` and `intake_completeness_calculator` independently check conditional L-branch fields so failures surface at both the schema gate and the KPI score.
- Stage C absent → `declaration_verification["live_system_access"] = "not_verifiable"` set immediately on `AuditState`; Phase 1 does not need to re-detect it.

---

## ✅ Group 3: Core Orchestrator and Verifier (Tier 1) — COMPLETE

**Current state:** All files present on disk. Smoke-tested end-to-end (exit 0). No IDE diagnostics.

### Files created
| File | Purpose |
|------|---------|
| `aaa/tools/csp_solver.py` | `build_phase_csp(state) → Problem`; `solve_phase_plan(state) → dict` wrapping `python-constraint` (§6.2) |
| `aaa/tools/completeness_score.py` | KPI 1 rubric checker over admitted phase artefacts T02–T16 (§9.1) |
| `aaa/tools/regulatory_coverage.py` | KPI 2 article checklist: Arts. 9, 10, 13, 14, 15, 17, 43; Annex III; GPAI 51–55 (§9.1) |
| `aaa/agents/tier1/orchestrator.py` | `Orchestrator(BaseAgent)` — 9-node LangGraph `StateGraph`; `_InMemoryCheckpointer` offline / `PostgresSaver` production |
| `aaa/agents/tier1/verifier.py` | `Verifier(BaseAgent)` — rubric critique loop; deterministic offline path; LLM path via LiteLLM (litellm); max 2 reruns before `escalate_hitl` |
| `aaa/agents/tier1/regulatory_rag.py` | **Fleshed out** — offline KB covering Arts. 9/10/13/43/Annex III/GPAI 51; lazy LlamaIndex+Qdrant in production |

### What was built
- **`csp_solver`** — `build_phase_csp` encodes the full §6.2 catalogue (9 hard constraints: LLM routing, biometrics, special-cat data, high-risk P5, prohibited halt, etc.); `solve_phase_plan` returns the most conservative (M-preferring) solution; raises `ValueError` on over-constraint (triggers HITL).
- **`completeness_score`** — weighted rubric (M=1.0, O=0.5); matches `phase_status` template IDs against admitted `phase_artefacts`; `completeness_score_breakdown()` emits per-template rows for T17/T18.
- **`regulatory_coverage`** — `ARTICLE_SET` per risk tier × LLM flag; counts admitted artefact citations + compliance_matrix non-PENDING verdicts; `regulatory_coverage_breakdown()` emits covered/missing lists.
- **`Orchestrator`** — 9 graph nodes (`stage_0`, `plan`, `phase_1`, `route`, `parallel_phases`, `phase_5`, `compliance_matrix`, `hitl_checkpoint`, `phase_6`); `_node_plan` expands CSP phase-variable output to template-ID level via `_PHASE_TO_TEMPLATES`; sequential fallback runner when LangGraph not installed; all phase nodes are stubs that will be replaced by real agents in Groups 4–10.
- **`Verifier`** — four-dimension offline rubric (non-empty, non-empty dict, URI linkage); LLM path builds structured JSON prompt for four-dimension critique; `_decide_verdict` maps issues/notes/rerun-count to verdict code.
- **`RegulatoryRAG`** — offline KB + keyword→article lookup; `_vector_search` lazily loads LlamaIndex VectorStoreIndex from Qdrant; `_offline_search` word-overlap scoring as fallback; both paths return `{text, source, article, score}` dicts.

### Key design decisions
- `phase_status` is keyed by **template IDs** (not CSP variable names) so `completeness_score` and `phase_artefacts` share the same key space.
- `Orchestrator._run_sequential` provides a full offline path (no LangGraph required) so CI and the Streamlit demo work without Docker services.
- `Verifier` LLM path uses `response_format={"type": "json_object"}` for structured critique output; falls back to offline deterministic check on any LLM exception.
- `RegulatoryRAG` LLM imports are `# pragma: no cover` lazy imports inside try/except so the module imports cleanly even if llama-index/qdrant-client are not installed.

---

## ✅ Group 4: Phase 1 — Scope and Risk Classifier — COMPLETE

**Current state:** All files present on disk. Smoke-tested end-to-end (exit 0, 6/6 tests). No IDE diagnostics.

### Files created
| File | Purpose |
|------|---------|
| `templates/T02_system_card.json` | JSON Schema — provider/deployer identity, modality, deployment context, `declaration_verification` map (Art. 13 §3) |
| `templates/T03_annex_iii_mapping.json` | JSON Schema — list of `AnnexIIIEntry` with provenance (Annex III) |
| `templates/T04_risk_tier_decision.json` | JSON Schema — `risk_tier` + rationale + Art. 6 §3 derogation (Art. 6, Art. 7) |
| `templates/T05_art43_decision.json` | JSON Schema — `art43_select` final output; binding statement (Art. 43) |
| `aaa/tools/annex_iii_classify.py` | Keyword/rule classifier over Annex III catalogue; lazy LlamaIndex+Qdrant in production; returns `list[AnnexIIIEntry]` with `provenance` |
| `aaa/tools/declaration_diff.py` | Deep-diff of declared vs verified scalar fields; `diff_annex_iii_sections` for section-level diff; any `"mismatch"` triggers HITL |
| `aaa/agents/tier2/scope_agent.py` | `ScopeAgent(BaseAgent)` — Phase 1 declaration verifier; loads T01a/T01b; enforces Art. 5 gate; classifies Annex III; emits T02–T05; returns `Report` with `declaration_verification_delta` |

### What was built
- **T02_system_card** — provider identity, verified modality, `declaration_verification` map, Art. 5 flag, GPAI screening result.
- **T03_annex_iii_mapping** — full `entries[]` array with `provenance`, `confidence`, `derogation_claimed`; `verified_risk_tier`; `art5_prohibited` flag.
- **T04_risk_tier_decision** — declared vs verified risk tier; Art. 6 §3 derogation fields; Annex III sections confirmed; RAG citation list.
- **T05_art43_decision** — final Art. 43 procedure + binding statement; `preview_procedure` + `delta_from_preview` flag (triggers HITL if true); input snapshot for reproducibility.
- **`annex_iii_classify`** — 8-section keyword catalogue; offline path scores by keyword overlap; RAG path blends `rag_score×0.6 + keyword_score×0.4`; returns entries sorted by provenance order then confidence desc. Declared sections below rejection threshold → `phase1_rejected`. Undeclared sections above detection threshold → `phase1_verified`.
- **`declaration_diff`** — compares scalar fields (modality, risk_tier, deployment_context, is_llm_or_agentic, provider_elects_third_party, gdpr_overlap, special_category_data, gpai_general_purpose). `diff_annex_iii_sections` returns per-section verdicts keyed `annex_iii_§{n}`.
- **`ScopeAgent`** — 11-step workflow: load intake → build description → classify Annex III → Art. 5 gate (raises `ScopeAgentError` on hit) → GPAI screen → verify modality → determine risk tier → `declaration_diff` → `art43_select` final → write T02–T05 → emit `Report`. Orchestrator `_node_phase_1_impl` calls real agent when `evidence_store` is provided; falls back to stub otherwise.

### Key design decisions
- Art. 5 prohibition check is a **hard halt**: `ScopeAgentError` is raised immediately, no artefacts are written, engagement is blocked.
- `annex_iii_classify` uses a **rejection threshold** (0.20): declared sections with no supporting evidence get `phase1_rejected` rather than being silently dropped — this makes the verification gap visible in T03 and triggers HITL.
- `Orchestrator.__init__` now accepts optional `evidence_store` and `regulatory_rag`; when present, the real `ScopeAgent` is instantiated; `_node_phase_1_impl` bridges async→sync via `asyncio.run()` / `ThreadPoolExecutor` fallback.
- All four templates use `additionalProperties: false` (draft-07 strict mode) matching the T01a/T01b convention.

---

## ✅ Group 5: Phase 2 — Data Governance Auditor — COMPLETE

**Current state:** All files present on disk. Smoke-tested end-to-end (exit 0). No IDE diagnostics.

### Files created
| File | Purpose |
|------|---------|
| `templates/T06_datasheet_for_datasets.json` | Gebru-2021 datasheet schema: motivation, composition, collection, preprocessing, uses, distribution, maintenance (Art. 10 §2–§3) |
| `templates/T07_data_quality_report.json` | Missingness, class balance, drift, PII scan results (Art. 10 §2, §4) |
| `templates/T08_special_category_data_log.json` | Art. 10 §5 lawful-basis log; special-category flag (Art. 10 §5, GDPR Art. 9) |
| `aaa/tools/data_profile.py` | ydata-profiling wrapper; pandas fallback; returns T07 `dataset_summary` dict (§4.1) |
| `aaa/tools/missingness_scan.py` | pandas-based; per-column missingness rates; returns T07 `missingness` dict (§4.1) |
| `aaa/tools/class_balance.py` | Pure-pandas class distribution + imbalance flag; returns T07 `class_balance` dict (§4.1) |
| `aaa/tools/pii_scan.py` | Presidio `AnalyzerEngine`; keyword-regex fallback; flags special-category data (§4.1) |
| `aaa/agents/tier2/data_auditor.py` | `DataAuditor(BaseAgent)` — Phase 2 Data Governance Auditor (Art. 10) |

### What was built
- **T06 schema** — all 7 Gebru-2021 sections required: `motivation`, `composition`, `collection_process`, `preprocessing_cleaning_labelling`, `uses`, `distribution`, `maintenance`; `additionalProperties: false` throughout.
- **T07 schema** — `dataset_summary`, `missingness`, `class_balance`, `drift` (optional), `pii_scan`, `overall_quality_verdict` (PASS/PASS_WITH_OBSERVATIONS/FAIL).
- **T08 schema** — `special_category_data_present`, `special_categories_detected`, `lawful_basis_entries` with per-category GDPR Art. 9 §2 basis, `art10_5_statistical_correction_applies`, `privacy_tier3_triggered`, `hitl_review_required`.
- **`data_profile`** — production path via ydata-profiling `ProfileReport(minimal=True)`; pandas fallback computes dtype summary, duplicate count, memory usage; returns T07 `dataset_summary` block.
- **`missingness_scan`** — iterates all columns; returns `missing_count`, `missing_pct`, `overall_missingness_pct`, `high_missingness_columns` (threshold default 20 %).
- **`class_balance`** — `value_counts` on target column; computes majority:minority ratio; severity bands: none / mild (<3×) / moderate (<10×) / severe (≥10×).
- **`pii_scan`** — Presidio path with `_SPECIAL_CATEGORY_ENTITIES` mapping Presidio entity types to GDPR Art. 9 categories; keyword-regex fallback over column names; both paths return `entities_found`, `special_category_data_detected`, `special_categories_found`.
- **`DataAuditor`** — 10-step workflow: load intake → load dataset → run 4 tools → detect special-category override → determine quality verdict → build T06/T07/T08 → store → emit `Report` with `declaration_verification_delta` (including `special_category_data` override + `privacy_tier3_triggered` flag).
- **Orchestrator** — `_node_parallel_phases_impl` bound method replaces `_node_parallel_phases` in both LangGraph and sequential runners; `_node_phase_2_impl` dispatches real `DataAuditor` when `evidence_store` is present; Phases 3/4 remain stubs.

### Key design decisions
- `pii_scan` keyword-regex fallback operates on **column names only** (not cell values) to avoid inadvertent PII exposure in logs; Presidio path samples first 200 rows and caps text to 10 000 chars per column.
- `DataAuditor._load_dataset` gracefully handles the common offline case (no dataset URI in dossier) by returning an empty DataFrame — all tools accept empty input without error.
- T08 is always written (even when `special_category_data_present = false`) so downstream Verifier can confirm the absence was checked, not just absent.
- `special_category_data` override in `declaration_verification_delta` propagates back to `AuditState.client_submission.stage_a` so Phase 5 GovernanceAgent sees the corrected value.

---

## ✅ Group 6: Phase 3 — Model Validation Agent — COMPLETE

**Current state:** All files present on disk. Smoke-tested end-to-end via `scripts/smoke_group6.py` (exit 0): Orchestrator dispatches `ModelValidator`, T09/T10/T11 artefacts persisted in EvidenceStore, all three payloads validate against their draft-07 JSON Schemas, verifier critiques carry the correct Article citations (Art. 13, Art. 15).

### Files created
| File | Purpose |
|------|---------|
| `templates/T09_model_card.json` | JSON Schema — architecture, training regime, performance metrics, known limitations (Art. 13 §3, Art. 15) |
| `templates/T10_explainability_report.json` | JSON Schema — SHAP/LIME/Grad-CAM outputs + interpretation (Art. 13 §1–§2) |
| `templates/T11_robustness_report.json` | JSON Schema — adversarial probe results, accuracy under perturbation (Art. 15) |
| `aaa/tools/metric_suite.py` | `metric_suite(...)` — accuracy/F1/AUC/calibration; sklearn path with pure-Python fallback |
| `aaa/tools/shap_explain.py` | `shap_explain(...)` — SHAP feature importance; variance-proxy fallback when `shap` unavailable |
| `aaa/tools/lime_explain.py` | `lime_explain(...)` — per-instance local explanations; empty-features fallback when `lime` unavailable |
| `aaa/tools/gradcam_explain.py` | `gradcam_explain(...)` — CV-only Grad-CAM heat-maps; no-op fallback when `pytorch-grad-cam` or `torch` unavailable |
| `aaa/tools/robustness_probe.py` | `robustness_probe(...)` — FGSM/PGD/text/tabular probes; `NOT_TESTED` verdict when `foolbox`/`textattack` unavailable |
| `aaa/agents/tier2/model_validator.py` | `ModelValidator(BaseAgent)` — Claude Opus; orchestrates the five tools; populates T09–T11; emits `Report` with `declaration_verification_delta.phase_artefacts` |
| `scripts/smoke_group6.py` | Offline smoke test — runs Orchestrator end-to-end, validates T09–T11 against their schemas, prints verifier critiques and final verdict |

### What was built
- **T09 schema** — `model_metadata`, `architecture`, `training`, `performance_metrics` (primary metric + per-metric values), `calibration`, `evaluation_dataset`, `known_limitations`, `art13_3_disclosures`, `art15_robustness_summary`.
- **T10 schema** — `technique` (shap/lime/gradcam/variance_proxy/none), `global_feature_importance`, `local_explanations`, `heatmaps`, `sample_size`, `tool_provenance`, `interpretation_notes`.
- **T11 schema** — `clean_accuracy`, `probes[]` (each with `attack_name`, `epsilon`, `adversarial_accuracy`, `success_rate`), `overall_robustness_verdict` (PASS / PASS_WITH_OBSERVATIONS / FAIL / NOT_TESTED), `min_adversarial_accuracy`, `skipped_reason`, `tool_provenance`.
- **`metric_suite`** — sklearn path computes accuracy, F1 (macro), AUC, ECE; pure-Python fallback handles offline runs and empty inputs without raising; returns dict directly slotable into T09 `performance_metrics`.
- **`shap_explain`** — `shap.Explainer` path for tabular/NLP; fallback computes per-feature std as a variance proxy and ranks features so T10 always carries usable global importance; never raises on missing optional deps.
- **`lime_explain`** — `LimeTabularExplainer.explain_instance` per row; fallback emits one `{instance_id, prediction:'unknown', top_features:[]}` entry per row so downstream schema validation still passes.
- **`gradcam_explain`** — guards on `torch`+`pytorch-grad-cam`; CV-only; returns `[]` when modality is not CV or libs missing so T10 stays valid.
- **`robustness_probe`** — modality-aware: foolbox FGSM/PGD for CV, textattack for NLP, perturbation sweep for tabular; verdict bands at 0.85/0.70; `NOT_TESTED` + `skipped_reason` when no model/labels supplied.
- **`ModelValidator`** — 6-step workflow: load intake → derive modality/task → run `metric_suite` → route to `shap`/`lime`/`gradcam` by modality → run `robustness_probe` → build T09/T10/T11 → store via `EvidenceStore.store_artefact` → emit `Report` whose `declaration_verification_delta.phase_artefacts` carries the three `ArtefactRef`s.
- **Orchestrator wiring** — `__init__` instantiates `self._model_validator = ModelValidator(...)` when `evidence_store` is provided; `_node_phase_3_impl` runs the real agent via the same thread-pool / asyncio pattern as Phase 2, falls back to mem-URI stubs on exception, skips entirely for `modality in {llm, agentic, gpai}` (Group 10 takes over via UAGF-TAM-L); writes per-tid verifier critiques with Article citations `{T09:[Art.13,Art.15], T10:[Art.13], T11:[Art.15]}`.

### Key design decisions
- Every tool has a **soft-fail fallback path** so `AAA_OFFLINE_MODE=true` runs never raise on missing heavy dependencies (`shap`, `lime`, `foolbox`, `textattack`, `torch`, `pytorch-grad-cam`); the schema-valid output instead carries an explicit `technique:"none"` / `overall_robustness_verdict:"NOT_TESTED"` marker plus a `skipped_reason`, so the Verifier and Phase 6 Report Architect can surface the gap to HITL.
- `ModelValidator` is **skipped, not stubbed, for LLM/agentic/GPAI modalities** — the Orchestrator routes those engagements to Group 10's UAGF-TAM-L branch which owns Arts. 13/15 evidence for generative systems; the Phase 3 stub block stays in place so `phase_artefacts` always contains T09/T10/T11 keys for compliance-matrix assembly.
- Article citations are attached at the Orchestrator layer (`_ARTICLES_BY_TID`) rather than inside the agent so the citation map remains a single audited surface for the Verifier and the Compliance Matrix node.
- The smoke test (`scripts/smoke_group6.py`) bypasses `IntakeValidator` (which expects MinIO URIs) by seeding `intake_completeness_score=0.95` directly on `client_submission`; this keeps Group 6 verification focused on Phase 3 dispatch and artefact integrity without coupling to Stage 0 plumbing.

---

## ✅ Group 7: Phase 4 — Output Fairness Tester — COMPLETE

**Current state:** All files present on disk. Smoke test passes (exit 0). No IDE diagnostics.

**Depends on:** Group 3 (Verifier), Group 4 (Phase 1 sets `annex_iii_mapping`). Phase 4 runs in parallel with Phases 2–3 on the standard branch; SKIPPED on the L-branch.

### Files created
| File | Purpose |
|------|---------|
| `aaa/agents/tier2/output_fairness.py` | `OutputFairnessTester(BaseAgent)` — runs 5 fairness/toxicity tools; builds T12, T13; emits `Report` |
| `aaa/tools/demographic_parity.py` | Selection-rate parity across groups; fairlearn/pure-Python fallback |
| `aaa/tools/equal_opportunity.py` | True-positive-rate gap; fairlearn/pure-Python fallback |
| `aaa/tools/disparate_impact.py` | EEOC four-fifths-rule ratio; aif360/pure-Python fallback |
| `aaa/tools/subgroup_metrics.py` | Per-group accuracy/SR/TPR/FPR breakdown |
| `aaa/tools/toxicity_classifier.py` | Detoxify wrapper; 200-prediction sample; keyword-regex fallback |
| `templates/T12_output_fairness_report.json` | JSON Schema (draft-07) for Output Fairness Report |
| `templates/T13_output_sampling_log.json` | JSON Schema (draft-07) for Output Sampling Log |
| `scripts/smoke_group7.py` | End-to-end smoke test — asserts T12/T13 stored, schema-valid, verdicts consistent |

### Files modified
| File | Change |
|------|--------|
| `src/agents/tier1/orchestrator.py` | Added `_output_fairness` init; `_node_phase_4_impl`; replaced P4 stub with real call |

### What was built
- **Four fairness metric tools** (`demographic_parity`, `equal_opportunity`, `disparate_impact`, `subgroup_metrics`) — each returns a typed dict with `metric`, `verdict` (`PASS/PASS_WITH_OBSERVATIONS/FAIL/NOT_TESTED`), and group-level breakdowns. Pure-Python fallback when fairlearn/aif360 unavailable.
- **Toxicity classifier** (`toxicity_classifier`) — wraps `Detoxify("original")`; caps at 200 predictions per §4A T13 spec; keyword-regex fallback when detoxify not installed.
- **T12 / T13 JSON Schemas** (draft-07) — T12 covers four fairness metric families + Art. 10 §2(f) / Art. 15 §1 compliance notes; T13 covers prediction sample + discriminatory-pattern flags + HITL trigger.
- **`OutputFairnessTester`** — async `process(Dispatch) → Report`; derives worst-band aggregate verdict; sets `hitl_required` on FAIL or discriminatory flag; stores artefacts via `EvidenceStore`.
- **Orchestrator wiring** — `_output_fairness` instantiated in `__init__` with graceful fallback; `_node_phase_4_impl` follows the same async-in-executor pattern as P2/P3; stub fallback preserved when agent is unavailable.

### Key design decisions
- **Worst-band aggregation** — overall fairness verdict = worst of {dp, eo, di, sg} verdicts; NOT_TESTED is overridden by any real verdict.
- **Pure-Python fallbacks** — all five tools work offline without external ML libraries; no hard dependencies on fairlearn, aif360, or detoxify.
- **HITL trigger** — any fairness FAIL or discriminatory-pattern flag sets `hitl_required=True` in the Report delta and propagates to orchestrator state.
- **Sampling cap** — T13 hard-caps at 200 predictions per §4A spec; `first_n` is the default strategy.

---

## ✅ Group 8: Phase 5 — Governance Agent (S4 Integration) — COMPLETE

**Current state:** All files present on disk. Smoke-tested end-to-end via `scripts/smoke_group8.py` (exit 0): `cgsa_pull` loads the offline fixture, `cgsa_ingest` validates the §5.4 payload against the vendored schema, T14 and T15 artefacts are persisted in the EvidenceStore, both payloads validate against their draft-07 JSON Schemas, risk-tier cross-check / CSP-failure verdict / Tier-3 spawn flags / HITL triggers are surfaced correctly. No IDE diagnostics. Group 7 smoke test still passes (no regression in orchestrator wiring).

### Files created
| File | Purpose |
|------|---------|
| `templates/T14_governance_findings.json` | JSON Schema (draft-07) — lift of `aaa_phase5_handoff` + domains/controls/hard-constraint results + risk-tier match + Tier-3 spawn recommendations (Art. 9, 10, 13, 14, 17) |
| `templates/T15_monitoring_logging_review.json` | JSON Schema (draft-07) — Annex IV §6/§7/§9 ops review against Art. 12 / 17 / 72 |
| `aaa/tools/cgsa_pull.py` | HTTP client; pulls CGSA payload from `{S4_CGSA_BASE_URL}/api/v1/assessments/{id}` with 5-attempt exponential back-off, `X-Schema-Version` pinning, 404 → HITL, 401 → re-auth surface; offline mode (`AAA_OFFLINE_MODE=true` or `CGSA_FIXTURE_DIR`) reads `{id}.json` from disk |
| `aaa/tools/cgsa_ingest.py` | `schema_validate(payload, "1.0.0")` against the canonical `schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json` (jsonschema path + shallow-required fallback); maps every §5.4 row into a `state_delta`; aggregates low-confidence controls; CSP failure → forces `cgsa_phase5_verdict=FAIL`; emits typed `RemediationItem` list |
| `aaa/agents/tier2/governance_agent.py` | `GovernanceAgent(BaseAgent)` — Claude Opus; orchestrates pull + ingest → risk-tier cross-check → Tier-3 spawn decisions → T14 + T15 build → EvidenceStore writes → `Report` with full §5.4 hydration on `declaration_verification_delta`; `_escalate_report` surface for pull/ingest failure |
| `scripts/fixtures/cgsa/smoke-group8-001.json` | Offline CGSA fixture — high-risk system, csp_satisfiable=false, 1 blocking finding (C07), 1 low-confidence control (C30), 1 required follow-up |
| `scripts/smoke_group8.py` | Offline smoke test — pulls fixture, runs GovernanceAgent, validates T14/T15 against their schemas, asserts §5.4 hydration keys / CSP-fail verdict / risk-tier match / Tier-3 spawns / HITL trigger |

### Files modified
| File | Change |
|------|--------|
| `src/agents/tier1/orchestrator.py` | Added `self._governance_agent` init (graceful fallback); new `_node_phase_5_impl` bound method dispatches the real agent via the async-in-executor pattern shared with Phases 2–4 and lifts the full §5.4 delta back onto `AuditState`; LangGraph node and sequential runner now point at `_node_phase_5_impl`; stub `_node_phase_5` preserved as fallback |

### What was built
- **T14 schema** — required: `engagement_id`, `cgsa_schema_version`, `cgsa_metadata`, `overall_scores`, `phase5_verdict`, `phase5_narrative_summary`, `blocking_findings_count`, `blocking_findings`, `positive_findings`, `low_confidence_controls`, `domains`, `hard_constraint_results`, `remediation_roadmap`, `risk_tier_match`, `tier3_spawn_recommendations`, `generated_at`. `additionalProperties: false` throughout.
- **T15 schema** — required: `engagement_id`, `monitoring_evidence`, `logging_evidence`, `post_market_monitoring`, `art12_record_keeping`, `art17_qms`, `art72_post_market_plan`, `overall_ops_verdict`, `generated_at`. Each Art. block carries a `status` ∈ {PASS, PASS_WITH_OBSERVATIONS, FAIL, NOT_APPLICABLE} plus rationale + evidence refs.
- **`cgsa_pull`** — 5-attempt exponential back-off (1–32 s) on 5xx/network; immediate `not_found` on 404; offline path reads `{CGSA_FIXTURE_DIR}/{assessment_id}.json` and pins `schema_version` against `CGSA_SCHEMA_VERSION` (default `1.0.0`); `CGSAPullError(reason, details)` for every failure mode so `GovernanceAgent._escalate_report` can surface a clean HITL trigger.
- **`cgsa_ingest`** — `IngestResult(payload, state_delta, low_confidence_controls, schema_errors, schema_version)`; validation strict-mode raises, non-strict returns errors on the result; `state_delta` contains all `cgsa_*` keys mapped on `AuditState` plus typed `remediation_roadmap` and inferred `harmonised_standards_applied` flag (true when any D3 control cites ISO 42001).
- **`GovernanceAgent`** — 8-step workflow: 1) pull (or accept inline payload from state), 2) ingest, 3) risk-tier cross-check, 4) Tier-3 spawn decisions, 5) T14 build, 6) T15 build, 7) EvidenceStore writes, 8) Report emit. HITL aggregation: `phase5_verdict=FAIL ∨ csp_satisfiable=false ∨ risk_tier mismatch ∨ low_confidence>0 ∨ T15 ops FAIL ∨ blocking follow-up`.
- **Tier-3 spawn rules** (§3.3): Cyber when `risk_tier=high` OR Phase 3 robustness verdict ∈ {FAIL, NOT_TESTED}. Privacy when `gdpr_overlap=true` OR `special_category_data=true` OR Annex III §1 (biometric).
- **Orchestrator wiring** — `_node_phase_5_impl` bridges async→sync exactly as P2/P3/P4 (asyncio.run / ThreadPoolExecutor fallback), pulls T01a/T01b URIs from `phase_artefacts`, threads Phase 1 `risk_tier` and Phase 3 `T11` verifier verdict into the Dispatch `declaration_summary`, lifts every §5.4 key from the delta back onto AuditState, writes per-tid verifier critiques with citations `[Art.9, Art.10, Art.13, Art.14, Art.17, Art.72]`, falls back to the stub on any unhandled exception.

### Key design decisions
- **Pull is the only network-touching surface**; `cgsa_ingest` and `GovernanceAgent` are pure functions of the payload, so the entire offline path is deterministic and unit-testable.
- **`Orchestrator._node_phase_5_impl` accepts an inline `cgsa_payload` on the Dispatch `declaration_summary`** — this lets the Streamlit demo (and tests) short-circuit the pull when the payload is already on AuditState, while production runs still go through `cgsa_pull` with retry.
- **CSP failure is a hard override**: even when `aaa_phase5_handoff.phase5_verdict` is `PASS_WITH_OBSERVATIONS`, `csp_satisfiable=false` forces `cgsa_phase5_verdict=FAIL` per §6 step 6. This keeps the final-verdict logic in `_node_compliance_matrix` honest without a second pass.
- **T14 mirrors §5.4 verbatim** — no creative synthesis. The agent is an ingestion adaptor, not a rescorer. Phase 5 narrative is verbatim from CGSA so reproducibility is trivial.
- **T15 leans on Annex IV evidence first, CGSA D6 second** — `cgsa_cross_references` lift D6 controls into the article rationale so the Verifier can trace each ops verdict to a concrete CGSA control. Missing monitoring/logging/post-market plan downgrades the verdict to `PASS_WITH_OBSERVATIONS`; all three missing → `FAIL` + HITL.
- **`additionalProperties: false` on every T14/T15 object** — matches the T02–T13 convention so any field drift from the agent is caught immediately by the smoke-test schema check.

---

## ✅ Group 9: Phase 6 — Report Architect — COMPLETE

**What was built:**
- `templates/T17_compliance_matrix.json` — JSON-Schema (draft-07) for the Article × Verdict × evidence-URI table. Covers Arts. 9, 10, 13, 14, 15, 17, 43, 50, 72, Annex III/IV, GPAI 51–55. Each row carries `source_phase`, `supporting_template_ids`, `cgsa_control_ids`, `blocking_findings`, and optional `rationale`.
- `templates/T18_audit_report.json` — JSON-Schema (draft-07) for the master Annex IV-aligned conformity-assessment report. Embeds T01a–T17 by URI reference; carries KPI triads with `kpiN_band`, `art43_decision`, `executive_summary`, `remediation_roadmap`, `rendered_report` block (pdf + json URIs), and full `engagement_metadata`.
- `aaa/tools/template_render.py` — Generic template rendering utility: loads `templates/<id>.json`, validates with `jsonschema` (skips gracefully if absent), renders via jinja2 HTML partial when available (falls back to `json.dumps`), persists payload + fragment to `EvidenceStore`, returns `ArtefactRef`.
- `aaa/tools/report_render.py` — Stitches T18 payload into a PDF (ReportLab A4 canvas with page-overflow handling) and a machine-readable JSON artefact; text-fallback renderer when ReportLab is absent; both URIs returned as `{pdf_uri, pdf_bytes_size, json_uri, renderer}`.
- `aaa/agents/tier2/report_architect.py` — `ReportArchitect(BaseAgent)`: deterministic (no LLM). Builds T17 from `compliance_matrix` + `verifier_critiques` + `phase_artefacts` threaded through `declaration_summary`; derives per-article `source_phase` from `_ARTICLE_PHASE` map; builds T18 with KPI bands, executive summary, embedded artefacts, and `rendered_report` block; calls `template_render` × 2 and `report_render` × 1; emits `Report` with `final_verdict` in `declaration_verification_delta`.
- `aaa/agents/tier1/orchestrator.py` — Wired `self._report_architect = ReportArchitect(...)` in `__init__`; added `_node_phase_6_impl` bound method (real agent dispatch with thread-pool asyncio pattern + stub fallback); updated both `_build_graph` and `_run_sequential` to use `_node_phase_6_impl`.
- `scripts/smoke_group9.py` — Instantiates `ReportArchitect` directly; seeds a synthetic `high`-risk engagement (9-article compliance matrix, 14 admitted artefacts); validates T17/T18 against their schemas; asserts all in-scope articles appear in `T17.articles`; checks `rendered_report.json_uri` non-empty and `renderer` in `{reportlab, text_fallback}`; verifies `tool_calls`; exits 0. Regression: `smoke_group7.py` and `smoke_group8.py` still exit 0.

### Key design decisions
- **T17 assembled from `compliance_matrix` dict on `AuditState`** — the `_node_compliance_matrix` node (already fully implemented in the Orchestrator) populates `state["compliance_matrix"]` with `{Article: Verdict}` before Phase 6 runs; `ReportArchitect` reads it verbatim, so there is a single source of truth and no redundant verdict calculation.
- **`template_render` is non-strict by default** — schema violations log a warning but do not abort; the `strict=True` flag is available for production; this lets offline smoke tests still produce artefacts even when optional fields drift.
- **`report_render` returns a unified metadata dict** — both the PDF path and the JSON path are returned so T18's `rendered_report` block is always populated regardless of which renderer ran; the `renderer` field (`reportlab` vs `text_fallback`) gives auditors full provenance.
- **Phase 6 is fully deterministic** — no LLM call; all article-to-phase attribution is driven by `_ARTICLE_PHASE` lookup table; executive summary is templated from KPI + verdict data; this ensures reproducibility and keeps latency near-zero in offline mode.

---

## ✅ Group 10: Tier 3 — Specialist Sub-Agents — COMPLETE

**Current state:** All files present on disk. Import checks pass. Orchestrator wires all three Tier-3 agents (exit 0). Group 9 smoke test still passes (no regression). No IDE diagnostics.

**Depends on:** Group 3 (Orchestrator spawns these on demand from Phase 5), Group 5 (`pii_scan` reused by Privacy Sub-Agent), Group 6 (`robustness_probe` reused by Cyber Sub-Agent). Spawning conditions: UAGF-TAM-L when `is_llm_or_agentic=true`; Cyber when `risk_tier=high` or Art. 15 gap; Privacy when `gdpr_overlap=true` or `special_category_data=true` or Annex III §1.

### Files created
| File | Purpose |
|------|---------|
| `aaa/agents/tier3/uagf_tam_l.py` | `UagfTamLBranch(BaseAgent)` — Claude Opus; replaces Phases 2–4 for LLM/agentic/GPAI; golden-set, RAGAs, groundedness, injection, trajectory; emits T16 (§3.3 #10) |
| `aaa/agents/tier3/cyber_agent.py` | `CyberSecurityAgent(BaseAgent)` — Claude Sonnet; extends T11 with deeper FGSM/PGD + prompt-injection probes; emits blocking finding on critical exploit (§3.3 #11) |
| `aaa/agents/tier3/privacy_agent.py` | `PrivacyDPOAgent(BaseAgent)` — Claude Sonnet; extends T08 with lawful-basis entries, DPIA cross-ref, PII deep-dive (§3.3 #12) |
| `aaa/tools/ragas_eval.py` | `ragas_eval(questions, contexts, answers) → dict` — faithfulness + answer relevance; `ragas` lib / pure-Python fallback |
| `aaa/tools/groundedness_check.py` | `groundedness_check(context, answer) → dict` — groundedness score; `trulens` / pure-Python fallback |
| `aaa/tools/prompt_injection_suite.py` | `prompt_injection_suite(target_uri, system_prompt) → dict` — injection + jailbreak probes; `garak` / deterministic fallback |
| `aaa/tools/trajectory_audit.py` | `trajectory_audit(traces, permitted_tools) → dict` — Langfuse trace parser; tool-call sequence analysis (§4.4) |
| `templates/T16_uagf_tam_l_evidence.json` | JSON Schema (draft-07) — golden-set, RAGAs, groundedness, prompt-injection, trajectory results (Art. 15; GPAI Arts. 51–55) |

### Files modified
| File | Change |
|------|--------|
| `aaa/agents/tier1/orchestrator.py` | Added `_uagf_tam_l`, `_cyber_agent`, `_privacy_agent` init (graceful fallback); `_node_uagf_tam_l_impl`, `_node_cyber_impl`, `_node_privacy_impl` bound methods; L-branch routing in `_node_parallel_phases_impl`; Tier-3 spawn dispatch after Phase 5 |

### What was built
- **`UagfTamLBranch`** — replaces Phases 2–4 for generative modalities; runs golden-set (naive exact-match pass/fail), RAGAs (faithfulness + answer relevance), groundedness, prompt-injection suite, and trajectory audit (agentic only); derives `PASS / PASS_WITH_OBSERVATIONS / FAIL` verdict; stores T16 in EvidenceStore; emits full `Report` with `declaration_verification_delta`.
- **`CyberSecurityAgent`** — loads existing T11 artefact from store, augments with deeper adversarial probes (CyberAgent-prefixed probe names) and injection probes for LLM/agentic; emits blocking finding + HITL trigger when `vulnerability_rate > 0.05`; recalculates `min_adversarial_accuracy`; updates T11 in store.
- **`PrivacyDPOAgent`** — loads existing T08; re-runs `pii_scan` on eval set (500-row deep-dive); merges special-category detections; generates stub lawful-basis entries (pending DPO review) when data is present but entries missing; appends compliance narrative; updates T08 in store.
- **Four L-branch tools** (`ragas_eval`, `groundedness_check`, `prompt_injection_suite`, `trajectory_audit`) — all pure-function with library/offline fallback so deterministic in `AAA_OFFLINE_MODE=true`.
- **Orchestrator wiring** — L-branch: `_node_parallel_phases_impl` routes to `_node_uagf_tam_l_impl` when `is_llm_or_agentic=true` and agent is available; stub fallback preserved. Phase 5: after GovernanceAgent completes, `spawn_cyber_subagent` / `spawn_privacy_subagent` flags trigger `_node_cyber_impl` / `_node_privacy_impl` in-band (no graph change needed).

### Key design decisions
- **Tier-3 agents extend, not replace, existing artefacts** — CyberAgent reads T11 and writes an enriched T11 back; PrivacyAgent reads T08 and writes an enriched T08 back. This keeps the verifier-critique map stable (same TIDs).
- **In-band spawn (no new LangGraph nodes)** — Cyber and Privacy sub-agents are called directly from `_node_phase_5_impl` after the GovernanceAgent completes, driven by the spawn flags in the delta. This avoids graph-topology changes and keeps the sequential fallback path correct.
- **L-branch replaces, not supplements, Phases 2–4** — `_node_parallel_phases_impl` returns immediately after `_node_uagf_tam_l_impl` for the L-branch; standard DataAuditor / ModelValidator / OutputFairness nodes do not run. This matches the §3.3 #10 specification.
- **All tools have offline fallbacks** — deterministic pure-Python paths ensure `AAA_OFFLINE_MODE=true` produces valid (if synthetic) results for every tool, enabling reproducible CI smoke tests without external network or ML library dependencies.

---

## ✅ Group 11: Final Integration and Evaluation — COMPLETE

**Current state:** All files present on disk. `scripts/smoke_group11.py` exits 0 with `final_verdict=PASS_WITH_OBSERVATIONS` for the UCI German Credit reference scenario. CLI entry point runs end-to-end. Streamlit demo importable (syntax-clean). `uagf-tam-templates` package: 11/11 tests pass. No IDE diagnostics in modified files.

**Depends on:** All groups 1–10. The UCI German Credit dataset (available at `data/`) is the reference case study for the end-to-end run.

### Files created
| File | Purpose |
|------|---------|
| `scripts/fixtures/uci_german_credit/stage_a.json` | Synthetic-but-valid T01a payload — tabular credit scorer, `declared_risk_tier=high`, `declared_annex_iii_sections=["5"]`, `deployment_context=b2b`, `cgsa_assessment_id="uci-german-credit-001"` |
| `scripts/fixtures/uci_german_credit/stage_b.json` | Synthetic T01b Annex IV dossier §1–§9 covering training data, model architecture, evaluation, deployment, risk management, monitoring |
| `scripts/fixtures/uci_german_credit/stage_c.json` | Synthetic T01c Stage C live-system access metadata |
| `scripts/fixtures/cgsa/uci-german-credit-001.json` | CGSA payload fixture loaded offline by `cgsa_pull`; schema-valid (`source_frameworks`/`maturity_label` enums fixed; `satisfied_constraints` as object array) |
| `scripts/smoke_group11.py` | End-to-end reference smoke — IntakeValidator → Orchestrator → final state; asserts 12-stage execution, KPI gates, T17/T18 schema validity, Art. 9 / Art. 43 / Annex III evidence traceability |
| `aaa/cli.py` | `python -m aaa.cli run --engagement-id <id> --intake-dir <path>` — wires IntakeValidator → Orchestrator; prints JSON summary; optional `--output-file`, `--cgsa-fixture-dir`, `--offline` flags |
| `aaa/ui/app.py` | Streamlit demo — Stage A/B forms driven by T01a/T01b schemas; live `intake_completeness_score` preview; full-run button; T17/T18 download buttons. Run with: `streamlit run aaa/ui/app.py` |
| `packages/uagf_tam_templates/pyproject.toml` | MIT-licenced PyPI package skeleton (hatchling backend; semver 0.1.0; jsonschema + jinja2 deps; pytest-cov ≥ 80 % gate) |
| `packages/uagf_tam_templates/src/uagf_tam_templates/__init__.py` | Loader API: `list_templates`, `schema_path`, `load_schema`, `validate`, `partial_env`, `render_partial`, `SchemaNotFoundError` |
| `packages/uagf_tam_templates/src/uagf_tam_templates/schemas/T*.json` | Packaged copies of all 20 T01a–T18 schemas |
| `packages/uagf_tam_templates/src/uagf_tam_templates/partials/T17_compliance_matrix.j2`, `T18_audit_report.j2` | Markdown Jinja2 partials for T17 / T18 |
| `packages/uagf_tam_templates/tests/test_loader.py` | 11 tests covering discovery, schema-validation, partial rendering, semver |
| `packages/uagf_tam_templates/README.md`, `LICENSE` | Install / usage / publish flow; MIT licence |

### Files modified
| File | Change |
|------|--------|
| `aaa/agents/intake_validator.py` | Replaced `art43_preview.procedure` attribute access with `art43_preview["procedure"]` (Art43Decision is a TypedDict, not a dataclass); same fix for `t01c_content["art43_preview_procedure"]` |

### What was built
- **UCI German Credit reference fixture** — full Stage A / Stage B / Stage C payloads sized to pass `intake_completeness_calculator` (KPI 0 = 1.00) and matching the CGSA fixture by `cgsa_assessment_id`. Validates against T01a, T01b, T01c schemas without warnings.
- **CGSA fixture** — re-uses the §10.2 fixture-mode loader from `cgsa_pull`. Required schema fixes: `source_frameworks` restricted to the 12-framework enum (replaced "ISO 23894" → "ISO 42001"); `maturity_label` restricted to {absent, initial, developing, defined, optimised} (replaced "managed" → "optimised"); `satisfied_constraints` reshaped from ID strings to objects with `control_id`/`control_name`/`required_score`/`actual_score`/`eu_ai_act_article`.
- **smoke_group11.py** — drives IntakeValidator (Stage 0 A/B/C) then `orch.run(initial_state)` to preserve T01a/T01b/T01c artefacts (calling `orch.process({...})` would re-initialise state and drop them). Asserts: 19 expected template IDs present; KPI 0 ≥ 0.80; KPI 1 ≥ 0.75; KPI 2 ≥ 75 %; `final_verdict ∈ {PASS, PASS_WITH_OBSERVATIONS, FAIL}`; T17 + T18 validate against packaged schemas; T17 rows for Art.9, Art.43, Annex_III have at least one evidence URI present in `phase_artefacts`. Reference run: `intake_completeness_score=1.00`, `completeness_score=0.88`, `regulatory_coverage_pct=88.9`, verdict `PASS_WITH_OBSERVATIONS`.
- **`aaa/cli.py`** — single `run` subcommand: loads Stage A/B[/C] from `--intake-dir`, stores raw payloads in `EvidenceStore`, runs `IntakeValidator.process()` → `Orchestrator.run()`, prints a JSON summary (`final_verdict`, `phase_artefacts`, `compliance_matrix`, KPIs, art43 decision) and optionally writes it to `--output-file`. Exit codes 0 / 2 (intake gate) / 3 (pipeline error).
- **`aaa/ui/app.py`** — wizard UI: Stage A field-by-field form sourced from the T01a `enum`s; Stage B JSON editor seeded with the fixture; live KPI 0 progress bar; "Run full audit" triggers the same pipeline as the CLI; displays compliance matrix, phase artefact URIs, three KPI metrics; offers three download buttons (full AuditState JSON, T17, T18).
- **`uagf-tam-templates` package** — distributable subset of `src/templates/` plus a clean loader API + Jinja2 partials for T17/T18. Tests cover discovery, schema validity, draft-07 acceptance/rejection, partial rendering, and semver. Publish flow documented in `README.md`.

### Key design decisions
- **Thread intake state directly into the orchestrator (no re-init).** `IntakeValidator.process()` returns a fully-populated `AuditState` carrying T01a/T01b/T01c references; passing it to `Orchestrator.run(initial_state)` preserves them. The convenience `Orchestrator.process({engagement_id, client_submission})` was kept for callers that only have a `ClientSubmission` and want a fresh state.
- **Treat `Art43Decision` as a TypedDict everywhere.** `art43_select_from_state` returns a dict; the previous `.procedure` attribute access in `IntakeValidator` was a leftover from an earlier dataclass design and was the first crash hit by the reference smoke.
- **`uagf-tam-templates` ships only schemas + partials, not Python tooling.** This keeps the package small, lets third-party renderers depend on it without pulling in the AAA agent stack, and isolates the public-API surface (`load_schema`, `validate`, `render_partial`).
- **CGSA fixture is curated to schema-pass, not to truly model an audit.** It exercises every required §5.4 hand-off field at maturity levels that produce a `PASS_WITH_OBSERVATIONS` verdict, so the smoke covers the full Phase 5 path without depending on a live S4 backend.

---

## ✅ Post-Group-11: ISO/IEC 42001 Ingestion Fix and Documentation Update — COMPLETE

### What was done

#### ISO/IEC 42001 ingestion (end-to-end)

| Task | Status |
|------|--------|
| Diagnosed silent `pdfplumber` failure on ISO/IEC 42001 PDF (0 pages) | ✅ |
| Switched to `pypdfium2>=5.8.0`; added to `requirements.txt` | ✅ |
| Added `_ISO_CLAUSE_NUM_RE`, `_ISO_CONTROL_NUM_RE`, `_ISO_TITLE_HEAD_RE` for split-line headings | ✅ |
| Added `_warn(...)` in `load_pdf_units()` and `_load_all_units()` for empty loader | ✅ |
| Added `load_dotenv()` at script startup via `python-dotenv` | ✅ |
| Added early import warm-up block (numpy, sklearn, nltk, qdrant_client) to avoid macOS Gatekeeper delays | ✅ |
| Ran full end-to-end ingestion: 715 corpus chunks (339 EU AI Act + 288 GDPR + 88 ISO) + 15 obligation-question points | ✅ |
| Verified idempotency: re-run skips all 715 chunks, zero OpenAI API calls | ✅ |

#### Documentation update

| File | What was added |
|------|---------------|
| `README.md` | §5a "Recent Improvements" table + corpus state table |
| `SETUP.md` | `pypdfium2` row in knobs table; auto-.env note; macOS Gatekeeper note; ingestion-specific troubleshooting table |
| `USER_MANUAL.md` | 4 new troubleshooting rows for ingestion; `.env` auto-load note in §7 |
| `ARCHITECTURE.md` | §3.1a "Regulatory Corpus — Ingestion Design" (PDF backend, split-line headings, idempotency, corpus counts) |
| `infra/runbook.md` | Warm-up step in S1 "Bring the stack up" procedure |
| `tasks.md` | This entry |
