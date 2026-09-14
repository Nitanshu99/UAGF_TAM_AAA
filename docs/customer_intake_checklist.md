# Customer Intake — Questions & Document Checklist

This is everything the AAA platform asks a customer to provide before an audit
engagement can run. Intake happens in the wizard in three customer-facing steps:

1. **Step 1 — Upload documents.** The customer uploads whatever documentation
   they have; the document-intelligence agent reads it and pre-fills the forms.
2. **Step 2 — 8 quick questions.** Facts the agent cannot reliably determine
   from documents alone (~2 minutes).
3. **Step 3 — Review & confirm.** The customer confirms/edits the pre-filled
   **Stage A** (scope & classification) and **Stage B** (Annex IV technical
   dossier) forms and uploads the supporting documents.

---

## 1. Documents we request

### Step 1 — Initial document upload

| Upload | What we ask for | Formats | Required? |
|---|---|---|---|
| Technical documents | Model card, technical spec, data sheet, risk assessment, system description — anything describing the AI system (multiple files allowed) | pdf, docx, doc, txt, md | Recommended (customer may continue without documents) |
| Model artefact | The trained model file — improves technical validation depth | pkl, joblib, onnx, pt, safetensors, zip | Optional |
| Datasets | Training or evaluation dataset files (multiple files allowed) | csv, parquet, json | Optional |

### Step 3 — Supporting documents (Annex IV mapped)

| Document | Annex IV / Article mapping | Applies to | Formats |
|---|---|---|---|
| Risk management documentation | §5 / Art. 9 — the risk management system file | All systems | pdf, doc, docx |
| EU Declaration of Conformity | §8 — signed declaration of conformity (if available) | All systems | pdf, doc, docx |
| Post-market monitoring plan | §9 / Art. 72 — post-deployment monitoring plan | All systems | pdf, doc, docx |
| System prompt | The system prompt used by the model | LLM / Agentic / GPAI | txt, md, json |
| RAG manifest | Vector-store schema and retrieval configuration | LLM / Agentic / GPAI | json, yaml, yml |
| Guardrail configuration | Content-filter or safety guardrail configuration | LLM / Agentic / GPAI | json, yaml, yml |
| Golden evaluation set | At least **50 Q&A pairs** for evaluation | LLM / Agentic / GPAI | json, csv |
| Agentic trace sample | JSON array of tool-call traces from the customer's own tracing (e.g. a Langfuse export): `[{"id": ..., "steps": [{"type": "tool_call", "tool_name": ..., "depth": ...}]}]` | Agentic only | json |

### Step 3 — Optional model / dataset artefacts

These deepen the technical audit but are not required:

| Artefact | Description | Formats |
|---|---|---|
| Training dataset | The dataset used to train the model | csv, parquet, json |
| Evaluation dataset | The dataset used to evaluate/test the model | csv, parquet, json |
| Model artefact | The trained model file | pkl, joblib, onnx, pt, safetensors, zip |
| Model metadata | Model card or metadata file | json, md, txt |

---

## 2. Questions we ask

### Step 2 — The 8 quick questions

| # | Question | Answer type |
|---|---|---|
| 1 | What is your role in relation to this AI system? (built/trained the model = Provider; deploying someone else's model = Deployer) | Multi-select: provider, deployer, distributor, importer, product_manufacturer, authorised_representative |
| 2 | Who are the end users of this system? | One of: b2b, b2c, public_sector, internal |
| 3 | Does this system process personal data? (data identifying individuals — names, IDs, locations, behaviour) | Yes/No |
| 4 | *(only if Q3 = yes)* Does it process special-category data? (health, biometrics, political/religious beliefs, racial/ethnic origin — GDPR Art. 9) | Yes/No |
| 5 | Is this a General-Purpose AI (GPAI) model? (foundation model / LLM for many tasks, Arts. 51–55) | Yes/No |
| 6 | Does this system fall under any Annex III high-risk categories? | Multi-select from the 8 Annex III sections (below) |
| 7 | Are you electing a voluntary third-party conformity assessment? (Art. 43 §1(b)) | Yes/No |
| 8 | Where is this system placed on the market or used? | Multi-select: placed_on_eu_market, gpai_placed_on_eu_market, established_in_eu, importer_in_eu, output_used_in_eu, none |

**Annex III categories offered in Q6:**

1. Biometric identification and categorisation of natural persons
2. Management and operation of critical infrastructure
3. Education and vocational training
4. Employment, worker management and access to self-employment
5. Access to and enjoyment of essential private/public services (e.g. credit, insurance)
6. Law enforcement
7. Migration, asylum and border control
8. Administration of justice and democratic processes

### Step 3, Stage A — Scope & classification (pre-filled from documents, confirmed by the customer)

**Identity and purpose**

| Field | What we ask | Notes |
|---|---|---|
| Legal provider name | Full legal name of the organisation that developed or places the system on the market | Art. 11 |
| System name | Commercial or internal name of the AI system | |
| Version | Semantic version (e.g. 2.1.0; leading "v" accepted) | |
| Intended purpose | What the system is designed to do, who uses it, in what context | Art. 13 — min. 20 characters |

**Classification**

| Field | What we ask | Options |
|---|---|---|
| AI modality | Primary technical type of the system | tabular, cv, nlp, time_series, llm, agentic, gpai |
| Self-assessed risk tier | Customer's own Art. 6 risk assessment | high, limited, minimal, gpai |
| Annex III high-risk categories | Every Annex III category that applies (Art. 6 §2) | The 8 sections above |
| Deployment context | Who uses the system directly | b2b, b2c, public_sector, internal |

**Flags**

| Field | What we ask | Notes |
|---|---|---|
| GDPR overlap | Does the system use/produce data identifying individuals? | Triggers GDPR Art. 35 / DPIA review |
| Special-category data | Health, biometric, political/religious, racial/ethnic data? | GDPR Art. 9, EU AI Act Art. 10 §5 |
| GPAI model | Is this a general-purpose foundation model? | Arts. 51–55 |
| Voluntary third-party assessment | Elect a notified-body assessment even if not required? | Art. 43 §1(b) |

**Not asked: the prior governance self-assessment.** A CGSA is filed by S4
against an organisation and a system, and its assessment id is minted there —
the client has never seen it, so the wizard no longer asks for it. Step 3
looks it up from the provider and system names already on the form and tells
the client what it found, in those words. See
`aaa/tools/cgsa_pull/discover.py`.

### Step 3, Stage A — Advanced compliance fields (FLI EU AI Act Compliance Checker; all optional)

Populating these gives a more precise scope gate.

| Field | What we ask | Options / notes |
|---|---|---|
| FLI-E2 · Art. 25 modifications | Modifications that trigger Provider status | name_trademark, intended_purpose_change, substantial_modification, none |
| FLI-HR1 · Annex I Section B | Sectoral product categories | civil_aviation_security, two/three-wheel vehicles, agricultural/forestry vehicles, marine equipment, rail interoperability, motor vehicles, civil aviation |
| FLI-HR2 · Annex I Section A | Product categories | machinery, toys, recreational craft, lifts, ATEX, radio equipment, pressure equipment, cableway, PPE, gas appliances, medical devices, IVD medical devices |
| FLI-HR3 | Is third-party conformity assessment legally required? | Yes/No |
| FLI-HR5 | Art. 6 §3 derogation claimed (no significant risk of harm)? | Yes/No + free-text rationale when claimed |
| FLI-R1 | GPAI meets the Art. 51 §2 systemic-risk threshold (>10²⁵ FLOPs)? | Yes/No |
| FLI-R2 | Art. 2 exclusion category, if any | military, third_country_law_enforcement, research_and_development, open_source, personal_use, none |
| FLI-R3 · Art. 5 prohibited practices | Any prohibited practice — **any selection halts the engagement** | subliminal manipulation, exploiting vulnerabilities, biometric categorisation, social scoring, predictive policing, facial-recognition DB scraping, emotion recognition in workplace/education, real-time remote biometrics, none |
| FLI-R4 · Art. 50 transparency triggers | Transparency-relevant behaviours | deepfake content, public-interest text, emotion/biometric categorisation, direct interaction with persons, synthetic content generation, none |
| FLI-R5 | Public-law body or private entity providing public services? | Triggers Art. 27 FRIA when combined with high risk |

### Step 3, Stage B — Annex IV technical documentation (written answers)

| Field | What we ask | Annex IV / Article | Minimum |
|---|---|---|---|
| General system description | Overall purpose, problem solved, who is responsible, who uses it | §1 | 50 chars |
| Model architecture / type | Technical type and version (e.g. "XGBoost classifier v1.2") | §1 | — |
| Design and development process | How the model was designed and trained: methodology, architecture choices, key iterations | §2 | 30 chars |
| Training data description | Datasets used for training/validation: source, size, date range, collection method | §2 / Art. 10 | 30 chars |
| Data governance measures | Data quality, access control, handling (anonymisation, consent, bias review) | §2 | 20 chars |
| Monitoring and control measures | Post-deployment monitoring: drift detection, human-oversight triggers, incident response | §3 | 20 chars |
| Logging capabilities | What logs the system produces, events recorded, retention period | §3 / Art. 12 | 10 chars |
| Performance metrics | Key metrics as JSON, e.g. `{"accuracy": 0.78, "auc": 0.82, "f1": 0.71}` (optionally with nested `robustness_metrics`) | §4 | valid JSON |
| Significant changes log | Changes since initial deployment, one per line | §6 | — |
| Harmonised standards applied | ISO / IEC / EU harmonised standards (comma-separated) | §7 | — |
| Other standards applied | Other technical or sector-specific standards | §7 | — |
| Tool inventory | *Agentic only* — names of tools/functions the system may call (used to flag unauthorised tool calls in the trajectory audit) | — | — |

**Data dictionary (recommended — drives the Art. 10 / Art. 15 fairness analysis)**

| Field | What we ask |
|---|---|
| Target column | Column the model predicts (selected from uploaded CSV header when available) |
| Sensitive feature columns | Protected attributes for non-discrimination testing (e.g. age, sex, nationality) |
| Favourable / positive label | The positive outcome value used for fairness analysis (e.g. "1") |

**Model metadata (required when a model artefact is uploaded — Art. 15)**

| Field | What we ask |
|---|---|
| Task type | What the model does (pre-filled from declared modality) |
| Model format | Serialisation format (pre-filled from uploaded filename) |
| Model framework | Library required to run the model (optional, e.g. sklearn) |

**Model provenance (LLM / agentic systems — Art. 11)**

Asked only for generative systems. If you run a model you do not own — a vendor
endpoint, or a base model plus your own adapter — there is no file to upload,
so we record what *identifies* the model instead. **We never ask you to send us
model weights.**

Everyone answers these six:

| Field | What we ask |
|---|---|
| How is the model made available? | Upload · registry pull · base + adapter · hosted endpoint · not provided |
| Task type | What the model does |
| Model provider | The vendor or registry serving it, not your internal name for it |
| Model identifier | Its exact id, written the way the vendor writes it |
| Version pin | A version that cannot change — commit SHA, dated snapshot, image digest or ARN. Not `latest` or `main`, which re-point to different weights over time |
| Licence and access | The governing licence, and whether access needs approval (and from whom) |

The remaining questions depend on your vendor, because what counts as an
unchangeable version differs:

| Provider | Version pin | Also asked |
|---|---|---|
| HuggingFace | Commit SHA | Repository id; gated/private status; for adapters the base repo, its SHA, the adapter method, and transformers / torch / peft versions |
| OpenAI | Dated snapshot id | Full `ft:…` id for fine-tunes; organisation and project; decoding settings |
| Azure OpenAI | Deployment + model snapshot + api-version | Resource endpoint and region; the deployment name (which is not the model name) |
| Anthropic | Dated model id | `anthropic-version` header; max_tokens; extended-thinking budget if enabled |
| Google Gemini | Pinned model version | AI Studio or Vertex AI; project and region (availability differs by region) |
| OpenRouter | Route slug + variant + upstream provider | Which upstream provider actually serves the route — one slug can be served by several at different quantizations |
| NVIDIA NIM | Container image digest | NGC model id; endpoint; optimisation profile and quantization |
| AWS Bedrock | Model ARN | Region; on-demand vs provisioned throughput; attached guardrail id and version |
| Self-hosted | Server image digest + weight revision | Endpoint; served model name; where the weights came from |

We also ask for your **decoding settings** (temperature, top_p, seed,
max_tokens). These are part of the model's identity for audit purposes: the
same weights at different settings produce materially different accuracy and
robustness results, so any figure we reproduce is conditional on them.

---

## 3. What is required vs optional — the completeness gate

Intake is scored with a weighted **Annex IV completeness score (KPI 0)**; the
engagement gate passes at **score ≥ 0.80**.

| Annex IV section | Weight | Fields counted |
|---|---|---|
| §1 General description | 0.20 | general_description, model_type |
| §2 Design and development | 0.15 | design_process, training_data_description, data_governance_measures |
| §3 Monitoring and control | 0.10 | monitoring_measures, logging_capabilities |
| §4 Performance metrics | 0.15 | accuracy_metrics |
| §5 Risk management (Art. 9) | 0.15 | risk_management_file_uri |
| §6 Lifecycle changes | 0.05 | lifecycle_change_log |
| §7 Standards applied | 0.10 | harmonised_standards |
| §8 EU declaration of conformity | 0.05 | eu_doc_uri |
| §9 Post-market monitoring plan | 0.05 | post_market_plan_uri |

**Conditionally required** (each missing item deducts from the score when applicable):

- For **llm / agentic / gpai** modalities: system prompt, RAG manifest, guardrail configuration, golden evaluation set.
- For **agentic** modality additionally: tool inventory.

**Hard stop:** selecting any Art. 5 prohibited practice (FLI-R3) halts the engagement.

---

*Source of truth: the wizard intake code — `aaa/ui/wizard/` (steps 1–3, Stage A/B
specs in `step3/stage_a/`, `step3/stage_b/`, upload specs in `constants.py`) and
`aaa/tools/intake_completeness_calculator/section_weights.py`.*
