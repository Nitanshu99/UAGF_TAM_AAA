# AAA — Autonomous AI Auditor: Multi-Agent System Architecture

> End-to-end design of the agentic system that consumes the S4 `uagf_cgsa_aaa_schema.json` payload and produces an EU AI Act conformity-assessment report compliant with **Articles 9, 43, and Annex III** of Regulation (EU) 2024/1689.
>
> This document synthesises two complementary source sets:
>
> **Academic foundation (governs methodology, evidence, KPIs)**
> 1. Mökander, J. et al. (2023). *Auditing Large Language Models: A Three-Layered Approach.* AI & Ethics, 4.
> 2. Koshiyama, A. et al. (2022). *Towards Algorithm Auditing.* Alan Turing Institute.
> 3. Wang, L. et al. (2024). *A Survey on Large Language Model Based Autonomous Agents.* Frontiers of Computer Science, 18(6).
> 4. Falco, G. et al. (2021). *Governing AI Safety through Independent Audits.* Nature Machine Intelligence, 3.
> 5. Gebru, T. et al. (2021). *Datasheets for Datasets.* CACM, 64(12).
> 6. European Parliament (2024). *EU AI Act, Articles 9, 43, Annex III.* OJ L 2024/1689.
>
> **MAS-engineering tactics (govern topology, tooling, runtime)**
> 7. n8n — *Multi-agent system: Frameworks & step-by-step tutorial* (Dec 2025)
> 8. dev.to — *How to Build Multi-Agent Systems: Complete 2026 Guide* (Jan 2026)
> 9. LangChain — *Choosing the Right Multi-Agent Architecture* (Jan 2026)
> 10. Anthropic — *How we built our multi-agent research system* (Jun 2025)

---

## 1. Design Philosophy

The AAA is built around eight non-negotiable principles:

| # | Principle | Source | Consequence in AAA |
|---|-----------|--------|---------------------|
| 1 | **Specialisation beats generalisation** | n8n, dev.to; Mökander's three-layer separation | Each of the 6 audit phases gets its own agent rather than a monolithic "auditor". |
| 2 | **Orchestrator-worker, not free-form chat** | Anthropic, LangChain; Wang 2024 §3 (planner-executor pattern) | A single Orchestrator decomposes the audit into subtasks; workers have isolated context windows. |
| 3 | **Tools are not agents** | n8n, LangChain | SHAP, Grad-CAM, fairness metrics, JSON-schema validators are deterministic MCP/function tools — they do not consume reasoning tokens. |
| 4 | **Evidence is durable, communication is lightweight** | Anthropic (filesystem hand-off), n8n (pass file IDs); Gebru 2021 (datasheets as durable artefacts) | Agents exchange artefact references in a shared **Evidence Store**, not large blobs in prompts. |
| 5 | **Verify, don't trust** | Anthropic (eval loops), dev.to; Falco 2021 (independent audit) | An independent Verifier agent critiques every phase output before it is admitted to the final compliance matrix. |
| 6 | **Open-source-first infrastructure** | thesis requirement | Every infrastructure component is OSI-approved or Linux-Foundation-stewarded (LangGraph, LiteLLM, PostgreSQL, MinIO, Valkey, Qdrant, OpenBao, OpenTofu, Langfuse, Grafana, Loki). The only externally-hosted dependencies are LLM provider APIs (Anthropic Claude, OpenAI GPT, DeepSeek, Mistral, or a local Ollama runtime — all interchangeable through LiteLLM). |
| 7 | **Academically grounded** | Mökander 2023, Koshiyama 2022, Wang 2024, Falco 2021, Gebru 2021, EU AI Act 2024 | Every architectural decision traces to either the required-reading list (§1.1) or an EU AI Act article (§3.5, §6.3). MAS-engineering blogs inform tactics; the academic literature governs methodology, evidence requirements, and KPIs. |
| 8 | **Client declarations are first-class evidence** | Mitchell 2019 (Model Cards), Gebru 2021 (Datasheets), Arnold 2019 (AI FactSheets); EU AI Act Art. 11 + Annex IV | The intake bundle is structured as the Annex IV §1–§9 technical documentation collected through a three-stage A/B/C wizard (§6 Stage 0). Phase 1 *verifies* declared values rather than originating them; declared/verified mismatches are first-class HITL triggers (§6.2, §8.4). |

Token economics from Anthropic's data — multi-agent systems use ≈15× the tokens of single-agent chats — are accepted because each engagement is a high-value B2B audit (€25k–€180k per the consultancy fee bands), justifying the spend.

### 1.1 Academic Grounding Map

The architectural choices below trace directly to the thesis required-reading list. This is the canonical citation map used in the thesis literature review chapter.

| Architectural decision | Primary academic source | What the source contributes |
|---|---|---|
| 6-phase audit protocol (Scope → Data → Model → Output → Ops/Governance → Report) | **Mökander 2023** three-layered approach (governance / model / application) | Decomposition principle: an AI audit is not a single act but a layered set of evidence-gathering steps. UAGF-TAM's Phase 5 ≈ governance layer; Phases 3–4 ≈ model layer; Phase 4 output testing ≈ application layer. |
| Phase 2 (Data) evidence template + datasheet validation tool | **Gebru 2021** (Datasheets for Datasets) | Defines the mandatory data-documentation fields the Phase 2 agent must extract and validate (motivation, composition, collection process, preprocessing, uses, distribution, maintenance). |
| 6 phase agents + 3 cross-cutting + 3 specialist topology | **Wang 2024** §4 (autonomous-agent role specialisation) + Anthropic (lead-agent + parallel subagents) | The role-specialisation taxonomy of Wang's survey directly maps onto the UAGF-TAM phases; Anthropic's lead-agent pattern provides the runtime topology. |
| Independent Verifier agent (LLM-as-judge gate) | **Falco 2021** (independent audit principle) + Anthropic eval-loop pattern | Falco's argument that AI audits must be performed by parties independent of the system developer translates, in an automated setting, to an independent agent that did not produce the artefact. |
| Completeness % and Regulatory Coverage % as primary KPIs (§9.1) | **Koshiyama 2022** (practitioner-gap analysis) | Koshiyama identifies that human auditors lack standardised completeness measures; the thesis fills this gap by defining and operationalising both metrics. |
| Article 9, 43, Annex III as the binding regulatory specification (§3.5, §3.6) | **EU AI Act 2024** | Primary legal text. Article 9 = risk-management system; Article 43 = conformity assessment procedure choice; Annex III = list of high-risk use cases. |
| Tier-3 specialists (Cyber, Privacy, L-Branch) | **Mökander 2023** application-layer audits + **Falco 2021** (independent security review) | Mökander's application layer explicitly demands red-teaming, prompt-injection testing, and DPIA cross-reference for LLM systems — these are the Tier-3 responsibilities. The exposé's UAGF-TAM-L pathway implements this layer. |
| `python-constraint` CSP for risk-tier routing (§6.2) | **EU AI Act 2024** Articles 6, 7, Annex III tier definitions | Formal encoding of the regulation's risk-tier obligations, executable and inspectable by regulator. |
| Streamlit Cloud demo + open-source artefact templates on GitHub | **Koshiyama 2022** call for community-shared audit tooling | Closes the practitioner gap by giving auditors something to use, not just read about. |
| Three-stage Annex-IV-aligned intake (Stage A triage → Stage B dossier → Stage C scoped access) | **EU AI Act 2024** Art. 11 + Annex IV §1–§9; **Mitchell 2019** (Model Cards); **Gebru 2021** (Datasheets); **Arnold 2019** (IBM AI FactSheets) | Annex IV defines the nine durable sections of the technical documentation a provider must compile; Model Cards, Datasheets, and FactSheets define the supplier-declaration pattern that populates those sections. AAA intake collects them explicitly so Phase 1 verifies, not classifies. |

---

## 2. Architectural Pattern Selection

The four LangChain patterns (Subagents, Skills, Handoffs, Router) were evaluated against the AAA's requirements:

| Requirement | Best-fit pattern | Why |
|-------------|------------------|-----|
| Phases 1–6 are largely independent, evidence is collected in parallel | **Subagents** (orchestrator-worker) | Matches Anthropic's research system; context isolation per phase |
| GPAI / LLM systems must take a different path (UAGF-TAM-L) | **Router** (one-hop) | Phase 1 routes to either the standard pipeline or the L-branch |
| Cybersecurity and DPO expertise is needed *only sometimes* | **Skills (progressive disclosure)** | These specialists are loaded on demand from Phase 5 |
| The final report must be produced after all phases complete | **Sequential pipeline** | Phase 6 is strictly downstream |

The chosen composite is therefore: **Orchestrator-Worker (Subagents) as the primary topology, with a Router fork at Phase 1 and Progressive-Disclosure Skills for legal/cyber specialists.** This mirrors Anthropic's lead-agent + parallel subagent design while keeping the deterministic ordering the EU AI Act conformity assessment demands.

---

## 3. Agent Roster (12 Agents)

The roster is partitioned into three tiers. Tier-1 agents are always active; Tier-2 agents run once per engagement; Tier-3 agents are spawned on demand.

Model assignments follow a cost-vs-capability rule: **Opus** for agents that synthesise heterogeneous evidence or render binding judgements; **Sonnet** for agents that interpret structured tool output against a regulatory rubric; **Haiku** for retrieval and small-context lookups.

### 3.1 Tier 1 — Cross-Cutting Services (always-on)

| # | Agent | Model | Primary responsibility |
|---|-------|-------|------------------------|
| 1 | **Orchestrator** | **Claude Opus** | Owns the audit plan, runs the python-constraint CSP, sequences phases, spawns/monitors subagents, decides parallel vs sequential dispatch. |
| 2 | **Verifier** | **Claude Opus** | Independent critic: judges every phase artefact against a rubric (factual accuracy, completeness, evidence linkage, regulatory citation correctness) before the Orchestrator admits it to the compliance matrix. |
| 3 | **Regulatory RAG** | **Claude Haiku** | Answers "what does Art. X §Y require?" on demand. Indexes EU AI Act, Annexes, delegated acts, harmonised standards (ISO/IEC 42001, 23894, 24029), GPAI Code of Practice. |

### 3.2 Tier 2 — Phase Agents (one per engagement)

| # | Agent | Model | UAGF-TAM phase | Primary responsibility |
|---|-------|-------|----------------|------------------------|
| 4 | **Phase 1 — Scope (Declaration Verifier)** | **Claude Sonnet** | P1 | **Verifies** the Stage-A triage declaration (modality, risk tier, Annex III sections, deployment context) collected at intake (§6 Stage 0); enforces the Art. 5 prohibition gate; performs GPAI screening; emits the `declaration_verification` map (match / mismatch / corrected). The `is_llm_or_agentic` flag is taken from the client declaration and only overridden if Phase 1 detects a verified mismatch (which raises HITL per §8.4). |
| 5 | **Phase 2 — Data Governance Auditor** | **Claude Sonnet** | P2 | Data quality, completeness, special-category-data scan, datasheet validation (Art. 10). |
| 6 | **Phase 3 — Model Validation Agent** | **Claude Opus** | P3 | Performance metrics, explainability (SHAP/Grad-CAM tool calls), robustness (Art. 13, 15). |
| 7 | **Phase 4 — Output Fairness Tester** | **Claude Sonnet** | P4 | Output sampling, demographic-parity / equal-opportunity / disparate-impact metrics, subgroup analysis. |
| 8 | **Phase 5 — Governance Agent** | **Claude Opus** | P5 | **Ingests `uagf_cgsa_aaa_schema.json`** from the upstream S4 CGSA, validates schema, lifts `aaa_phase5_handoff.blocking_findings` and `remediation_roadmap` into the compliance matrix. |
| 9 | **Phase 6 — Report Architect** | **Claude Sonnet** | P6 | Composes the conformity-assessment report (reportlab), executive summary, regulatory matrix, remediation roadmap aligned to Annex IV. |

### 3.3 Tier 3 — Specialist Sub-Agents (on-demand)

Tier-3 agents are required to satisfy Mökander 2023's **application-layer audit** obligations and Falco 2021's **independent security review** principle. Each is spawned only when its triggering condition fires, so steady-state token cost is bounded.

| # | Agent | Model | Triggered by | Primary responsibility | Academic justification |
|---|-------|-------|--------------|------------------------|------------------------|
| 10 | **UAGF-TAM-L Branch Agent** | **Claude Opus** | Phase 1 sets `is_llm_or_agentic = true` | Replaces Phases 2–4 with golden-set evaluation, faithfulness/grounding tests, prompt-injection & jailbreak suites, tool-call trajectory audit for agentic systems. | Mökander 2023 §4 (LLM-specific audit layer); exposé §2 Phase 1 UAGF-TAM-L requirement |
| 11 | **Cybersecurity Sub-Agent** | **Claude Sonnet** | Phase 5 when Art. 15 evidence is missing **or** risk tier = high **or** Cyber red-flag in any phase artefact | Adversarial robustness (FGSM/PGD on CV, injection on LLM), sandbox-escape probes for agentic systems. | EU AI Act Art. 15 (accuracy, robustness, cybersecurity); Falco 2021 (independent security audit) |
| 12 | **Privacy / DPO Sub-Agent** | **Claude Sonnet** | Phase 5 when GDPR overlap detected (special-category data, biometric data, Annex III §1 use case) | Art. 10 §5 lawful-basis check, DPIA cross-reference, retention & minimisation review. | EU AI Act Art. 10 §5; GDPR Art. 35 (DPIA); Mökander 2023 application-layer privacy audit |

**Why these three are non-negotiable for quality.** The exposé's required deliverable is *"EU AI Act-compliant"* reports (line 82). Compliance with Articles 10 §5, 15, and the GPAI/LLM evidentiary obligations cannot be discharged by the six phase agents alone without violating the Mökander/Falco independence principle: the agent that wrote the artefact cannot also be the agent that adversarially tests it. Removing any Tier-3 agent would either (a) leave a regulatory article unaudited, or (b) collapse audit and adversarial review into the same agent. Both are documented quality regressions.

### 3.4 Org Chart

```mermaid
flowchart TD
    classDef opus fill:#5b6cff,stroke:#2a3aad,color:#ffffff,stroke-width:1px
    classDef sonnet fill:#7fb069,stroke:#3f6a32,color:#0b1f08,stroke-width:1px
    classDef haiku fill:#f4c95d,stroke:#8a6a14,color:#2a1f06,stroke-width:1px
    classDef tier fill:#eef0f5,stroke:#6b7280,color:#111827,stroke-width:1px,stroke-dasharray:4 3

    T1[Tier 1 · Cross-Cutting]:::tier
    T2[Tier 2 · Phase Agents]:::tier
    T3[Tier 3 · Specialists]:::tier

    A1["1 · Orchestrator<br/>Opus"]:::opus
    A2["2 · Verifier<br/>Opus"]:::opus
    A3["3 · Regulatory RAG<br/>Haiku"]:::haiku

    A4["4 · Phase 1 · Scope / Risk Classifier<br/>Sonnet"]:::sonnet
    A5["5 · Phase 2 · Data Governance Auditor<br/>Sonnet"]:::sonnet
    A6["6 · Phase 3 · Model Validation<br/>Opus"]:::opus
    A7["7 · Phase 4 · Output Fairness Tester<br/>Sonnet"]:::sonnet
    A8["8 · Phase 5 · Governance Agent<br/>Opus"]:::opus
    A9["9 · Phase 6 · Report Architect<br/>Sonnet"]:::sonnet

    A10["10 · UAGF-TAM-L Branch<br/>Opus"]:::opus
    A11["11 · Cybersecurity Sub-Agent<br/>Sonnet"]:::sonnet
    A12["12 · Privacy / DPO Sub-Agent<br/>Sonnet"]:::sonnet

    T1 --- A1 & A2 & A3
    A1 --> T2
    T2 --- A4 & A5 & A6 & A7 & A8 & A9
    A4 -. routes LLM/agentic .-> A10
    A8 -. on-demand .-> T3
    T3 --- A10 & A11 & A12
```

### 3.5 Article 43 — Conformity Assessment Procedure Selection

Article 43 of Regulation (EU) 2024/1689 obliges the provider of a high-risk AI system to choose between two conformity-assessment procedures **before** placing the system on the market. The AAA Orchestrator must make this choice explicit in every audit report; the choice determines the report template and the downstream regulatory filings.

| Procedure | Annex | When required | AAA report section |
|---|---|---|---|
| **Internal control** | **Annex VI** | High-risk systems **except** those listed in Annex III §1 (biometrics), when the provider has applied the harmonised standards in full, or common specifications, or has otherwise complied with the requirements of Section 2 | "Article 43 § Procedure" → Annex VI declaration + technical-documentation index (Annex IV) |
| **Third-party assessment (notified body)** | **Annex VII** | (a) Annex III §1 biometric systems where the provider has *not* applied harmonised standards / common specifications, **or** (b) the provider has elected third-party review, **or** (c) the system falls under Union harmonisation legislation listed in Annex I Section A | "Article 43 § Procedure" → Annex VII notified-body section + conformity certificate placeholder |
| **Not applicable** | — | Limited- or minimal-risk systems; GPAI subject to Articles 51–55 separately | "Article 43 § Procedure" → "Not applicable; rationale: …" |

**Selection logic (Orchestrator, deterministic).** The `art43_select` tool (see §4.5) implements the following CSP-style rule. It runs **twice** per engagement:

1. **Preview** — at the end of Stage A intake, against the *declared* values (`declared_risk_tier`, `declared_annex_iii_sections`, `provider_elects_third_party`). The preview is shown to the client in the wizard ("If your declaration is correct, your conformity-assessment procedure will be: …") and is written to `T01a_stage_a_triage`.
2. **Final** — after Phase 1 has verified those declarations, against the *verified* values. The final decision is the binding one written to `T05_art43_decision`. If preview and final differ, the difference is recorded in `T01c_intake_completeness_report` and raised through the HITL "declaration mismatch" trigger (§8.4).

```python
def select_art43_procedure(state: AuditState) -> Art43Decision:
    if state.risk_tier in {"minimal", "limited"}:
        return Art43Decision(procedure="not_applicable",
                             rationale="System is not high-risk per Art. 6 / Annex III.")
    if state.risk_tier == "gpai":
        return Art43Decision(procedure="not_applicable",
                             rationale="GPAI obligations governed by Arts. 51–55, not Art. 43.")
    # high-risk path
    is_annex_iii_biometric = any(e.annex_iii_section == "1" for e in state.annex_iii_mapping)
    harmonised_applied = state.harmonised_standards_applied  # bool, set by Phase 5
    if is_annex_iii_biometric and not harmonised_applied:
        return Art43Decision(procedure="annex_vii_notified_body",
                             rationale="Annex III §1 biometric system without full application "
                                       "of harmonised standards — notified-body review required.")
    if state.provider_elects_third_party:
        return Art43Decision(procedure="annex_vii_notified_body",
                             rationale="Provider has elected third-party assessment.")
    return Art43Decision(procedure="annex_vi_internal_control",
                         rationale="High-risk system with harmonised standards applied in full; "
                                   "internal control procedure permitted by Art. 43 §2.")
```

The decision, its rationale, and the inputs that produced it are written to the Evidence Store as a discrete artefact (`art43_decision.json`) and rendered into the Phase 6 report as a binding statement.

### 3.6 Annex III — High-Risk Use-Case Taxonomy

Annex III categorisation is a **two-step process**: the client first declares the relevant sections in the Stage-A triage form (§6 Stage 0), and the Phase 1 Scope Agent then verifies each declared entry against the intake-bundle evidence and the Regulatory RAG corpus. Each mapping is one `AnnexIIIEntry`; every entry carries a `provenance` field so the Verifier and the regulator can tell whether a given section was declared, verified, corrected, or added by Phase 1. The mapping is the primary input both to the `risk_tier` decision (Annex III ⇒ high-risk unless Art. 6 §3 derogation applies) and to the Article 43 selector above.

| § | Annex III category | Typical use-case markers | Mandatory Tier-3 spawns | Example case in thesis |
|---|---|---|---|---|
| 1 | **Biometrics** (remote ID, categorisation, emotion recognition) | facial-recognition, fingerprint, voice ID | Privacy + Cyber | (not in thesis; flagged as out-of-scope) |
| 2 | **Critical infrastructure** | energy grid, water, traffic management | Cyber | Hamburg Hub live system (if applicable) |
| 3 | **Education and vocational training** | admissions scoring, exam grading | Privacy (minor data) | — |
| 4 | **Employment, workers management, self-employment** | CV screening, performance scoring | Privacy + Fairness deep-dive | UCI German Credit (proxy: employment-adjacent) |
| 5 | **Access to essential private/public services** | credit scoring, benefits eligibility, emergency triage | Privacy + Fairness deep-dive | **UCI German Credit (Case Study 1, Finance)** |
| 6 | **Law enforcement** | predictive policing, evidence assessment | Privacy + Cyber | — |
| 7 | **Migration, asylum, border control** | visa risk, document authenticity | Privacy + Cyber | — |
| 8 | **Administration of justice & democratic processes** | judicial decision support, electoral influence | Privacy + Cyber | — |

`AnnexIIIEntry` schema (used in `AuditState`, §5.1):

```python
class AnnexIIIEntry(TypedDict):
    annex_iii_section: Literal["1","2","3","4","5","6","7","8"]
    section_title: str                  # e.g. "Access to essential private services"
    use_case_marker: str                # short evidence string from intake docs
    confidence: float                   # 0.0–1.0 from Phase 1 verifier
    provenance: Literal[                # NEW — declared-vs-verified provenance
        "client_declared",              # in Stage A and confirmed by Phase 1
        "phase1_verified",              # silent in Stage A, added by Phase 1 with evidence
        "phase1_corrected",             # declared by client but section number adjusted
        "phase1_rejected"               # declared by client but evidence refutes it
    ]
    derogation_claimed: bool            # Art. 6 §3 derogation
    derogation_rationale: str | None    # required if derogation_claimed
```

The Regulatory RAG agent (§3.1 #3) holds the canonical Annex III text and returns it on demand to the Scope Agent. The Scope Agent ingests the client's declared sections from `client_submission.stage_a.annex_iii_declared`, then emits zero, one, or many `AnnexIIIEntry` items per engagement with the correct `provenance` value. Any entry with `provenance ∈ {phase1_corrected, phase1_rejected}` raises the "declaration mismatch" HITL trigger (§8.4). Emitting at least one entry with `derogation_claimed = false` forces `risk_tier = "high"`.

---

## 4. Tool Layer (Deterministic Capabilities)

Following the n8n/LangChain rule that *tools are not agents*, the AAA exposes a single MCP-style tool catalogue. Every tool is pure-function, version-pinned, and returns a structured payload that becomes part of the Evidence Store.

### 4.1 Data & Statistics Tools

| Tool | Library | Used by |
|------|---------|---------|
| `data_profile` | pandas-profiling / ydata-profiling | Phase 2 |
| `missingness_scan` | pandas | Phase 2 |
| `class_balance` | scikit-learn | Phase 2 |
| `drift_test` | evidently, scipy KS-test | Phase 2, Phase 4 |
| `pii_scan` | Presidio | Phase 2, Privacy Sub-Agent |

### 4.2 Model & Explainability Tools

| Tool | Library | Used by |
|------|---------|---------|
| `metric_suite` | scikit-learn, torchmetrics | Phase 3 |
| `shap_explain` | shap | Phase 3 |
| `gradcam_explain` | pytorch-grad-cam | Phase 3 (CV models) |
| `lime_explain` | lime | Phase 3 |
| `robustness_probe` | foolbox, textattack | Phase 3, Cyber Sub-Agent |

### 4.3 Fairness Tools

| Tool | Library | Used by |
|------|---------|---------|
| `demographic_parity` | fairlearn | Phase 4 |
| `equal_opportunity` | fairlearn | Phase 4 |
| `disparate_impact` | aif360 | Phase 4 |
| `subgroup_metrics` | fairlearn | Phase 4 |

### 4.4 LLM / Agentic Tools

| Tool | Library | Used by |
|------|---------|---------|
| `ragas_eval` | ragas | UAGF-TAM-L |
| `groundedness_check` | trulens | UAGF-TAM-L |
| `prompt_injection_suite` | garak, promptfoo | UAGF-TAM-L, Cyber |
| `trajectory_audit` | custom (Langfuse traces) | UAGF-TAM-L |
| `toxicity_classifier` | detoxify | UAGF-TAM-L, Phase 4 |

### 4.5 Governance & Reporting Tools

| Tool | Library | Used by |
|------|---------|---------|
| `csp_solver` | python-constraint | Orchestrator (phase-routing CSP, §6.2) |
| `schema_validate` | jsonschema | Phase 5 (S4 payload), Phase 6 (final report JSON) |
| `cgsa_pull` | custom (HTTP client; pulls `uagf_cgsa_aaa_schema.json` from S4) | Phase 5 |
| `cgsa_ingest` | custom (parses + validates the pulled CGSA payload) | Phase 5 |
| `annex_iii_classify` | custom (LlamaIndex over Annex III text + rule table §3.6) | Phase 1 |
| `art43_select` | custom (deterministic rule §3.5) | Orchestrator |
| `regulatory_search` | LlamaIndex over EU AI Act corpus | Regulatory RAG |
| `template_render` | jinja2 over 20 artefact templates (§4A) | All phase agents |
| `report_render` | reportlab, jinja2 | Phase 6 |
| `completeness_score` | custom (rubric checker, §9.1) | Verifier |
| `regulatory_coverage` | custom (article checklist, §9.1) | Verifier |
| `annex_iv_validator` | jsonschema (validates Stage B dossier against the Annex IV §1–§9 JSON Schema bundle) | Intake / Orchestrator |
| `intake_completeness_calculator` | custom (rubric checker; §9.1 KPI 3 on the populated Annex IV bundle) | Intake / Verifier |
| `declaration_diff` | custom (deep-diff between Stage-A declared values and Phase-1 verified values; emits `declaration_verification` map) | Phase 1 / Verifier |
| `triage_render` | jinja2 + jsonschema over `T01a_stage_a_triage` schema (the ~20-question Stage A form) | Intake UI |

---

## 4A. Artefact Template Registry (Deliverable 2)

The 20 standardised UAGF-TAM audit-evidence templates are first-class infrastructure: every phase agent's only legitimate output is a populated template instance, stored in the Evidence Store and rendered by `template_render`. Templates are MIT-licensed, version-pinned (semver), and published to `github.com/UAGF/uagf-tam-templates` as a separate Python package (`uagf-tam-templates`) so that the wider audit community can reuse them.

Each template is a JSON-Schema definition plus a Jinja2 rendering partial. The schema is the durable contract; the partial defines the human-readable rendering in the final PDF.

The intake artefacts (T01a / T01b / T01c) replace the previous single `T01_intake_manifest`. They mirror the three-stage intake (§6 Stage 0) and together populate Annex IV §1–§9 of Regulation (EU) 2024/1689.

| # | Template ID | Phase | Owning agent | Purpose | EU AI Act linkage |
|---|---|---|---|---|---|
| 1a | `T01a_stage_a_triage` | Intake (Stage A) | Orchestrator (Intake Validator) | ~20-question triage form: provider/deployer identity, intended purpose, declared modality, declared risk tier, declared Annex III sections, deployment context, `provider_elects_third_party`, GDPR-overlap declarations, CGSA `assessment_id`. Carries the preview Art. 43 decision. | Art. 11; Annex IV §1 |
| 1b | `T01b_annex_iv_dossier` | Intake (Stage B) | Orchestrator (Intake Validator) | Structured upload of the Annex IV §1–§9 technical documentation: (1) general description, (2) elements & dev process, (3) monitoring & control, (4) performance metrics, (5) risk-management file (Art. 9), (6) lifecycle changes, (7) standards applied, (8) EU declaration of conformity, (9) post-market monitoring plan. Conditional fields per modality (L-branch adds system prompt, RAG manifest, tool inventory, guardrail config, golden set). | **Art. 11 + Annex IV §1–§9** |
| 1c | `T01c_intake_completeness_report` | Intake (post-Stage B) | Intake Validator | Per-section Annex IV completeness scoring, list of missing/incomplete fields, the `intake_completeness_score` KPI (§9.1), and any preview-vs-final Art. 43 delta. Required ≥ 0.80 to unlock Phase 1. | Art. 11 |
| 2 | `T02_system_card` | P1 Scope | Scope | Provider, deployer, intended purpose, modality, deployment context — **populated by verifying** the corresponding T01a/T01b fields; carries the Phase-1 `declaration_verification` map. | Art. 13 §3 |
| 3 | `T03_annex_iii_mapping` | P1 Scope | Scope | List of `AnnexIIIEntry` (§3.6) | Annex III |
| 4 | `T04_risk_tier_decision` | P1 Scope | Scope | `risk_tier` + rationale + Art. 6 §3 derogation if any | Art. 6, Art. 7 |
| 5 | `T05_art43_decision` | P1 / Orch | Orchestrator | `art43_select` output (§3.5) | **Art. 43** |
| 6 | `T06_datasheet_for_datasets` | P2 Data | Data Auditor | Gebru-2021 datasheet (motivation, composition, collection, preprocessing, uses, distribution, maintenance) | Art. 10 §2, §3 |
| 7 | `T07_data_quality_report` | P2 Data | Data Auditor | Missingness, class balance, drift, PII scan results | Art. 10 §2, §4 |
| 8 | `T08_special_category_data_log` | P2 Data | Data Auditor + Privacy | Art. 10 §5 lawful-basis log, special-category flag | Art. 10 §5, GDPR Art. 9 |
| 9 | `T09_model_card` | P3 Model | Model Validator | Architecture, training regime, performance metrics, known limitations | Art. 13 §3, Art. 15 |
| 10 | `T10_explainability_report` | P3 Model | Model Validator | SHAP / Grad-CAM / LIME outputs + interpretation | Art. 13 §1, §2 |
| 11 | `T11_robustness_report` | P3 Model | Model Validator (+ Cyber) | Adversarial probe results, accuracy under perturbation | **Art. 15** |
| 12 | `T12_output_fairness_report` | P4 Output | Output Fairness | Demographic parity, equal opportunity, disparate impact, subgroup metrics | Art. 10 §2 (f), Art. 15 §1 |
| 13 | `T13_output_sampling_log` | P4 Output | Output Fairness | 200-prediction sample with discriminatory-pattern flags | Art. 15 §1 |
| 14 | `T14_governance_findings` | P5 Gov/Ops | Governance | Lift of S4 `aaa_phase5_handoff` (§5.4 map) | **Art. 9**, Art. 10, Art. 13, Art. 14, Art. 17 |
| 15 | `T15_monitoring_logging_review` | P5 Gov/Ops | Governance | Review of uploaded monitoring/logging docs (exposé's original Ops scope) | Art. 12, Art. 17, Art. 72 |
| 16 | `T16_uagf_tam_l_evidence` | P2L–P4L | UAGF-TAM-L Branch | Golden-set, RAGAs, groundedness, prompt-injection, trajectory results | Art. 15; GPAI Arts. 51–55 |
| 17 | `T17_compliance_matrix` | P6 Report | Report Architect | Article × verdict × evidence-URI table (Arts. 9, 10, 13, 14, 15, 17, 43; Annex III; GPAI 51–55) | All in-scope articles |
| 18 | `T18_audit_report` | P6 Report | Report Architect | Final Annex-IV-aligned PDF + machine-readable JSON; embeds T01a–T17 | Art. 11, Annex IV |

**Template lifecycle.** (1) Phase agent (or Intake Validator) calls `template_render(template_id, payload)`; (2) `template_render` validates `payload` against the template's JSON Schema; (3) on success, the rendered HTML/JSON fragment is written to MinIO; the SHA-256, URI, and `template_version` are appended to the `evidence` Postgres table; (4) the Verifier reads the JSON payload (not the rendering) for its rubric check; (5) Phase 6 composes T18 by stitching all admitted T01a–T17 instances through a master Jinja2 layout.

**Intake-template lifecycle (additional rules).** T01a is written at Stage A submission and is immutable thereafter (a new triage requires a new engagement). T01b is appended to throughout Stage B and is frozen once `intake_completeness_score >= 0.80`. T01c is regenerated on every Stage B append. T01a–c are gated by the `annex_iv_validator` tool and never enter LLM context until they pass schema validation (§9.3 Guardrails).

**Publication path (Deliverable 2).** `uagf-tam-templates` ships as: (i) PyPI package with the schemas and partials; (ii) GitHub repo with examples per template; (iii) one-page README per template explaining what to fill in, why, and where in the EU AI Act it satisfies. MIT licence, semver, ≥80% test coverage gate enforced in CI.

---

## 5. State Management & Communication

### 5.1 Shared State Object

A single `AuditState` object (LangGraph-style typed dict) is threaded through the graph:

```python
# ──────────────────────────────────────────────────────────────────────────────
# ClientSubmission — the three-stage intake bundle (Stage A + B + C artefacts)
# written to T01a/T01b/T01c before Phase 1 runs.
# ──────────────────────────────────────────────────────────────────────────────
class StageATriage(TypedDict):
    """~20-question form submitted at the start of each engagement (§6 Stage 0)."""
    provider_name: str
    deployer_name: str | None
    system_name: str
    version: str
    intended_purpose: str
    # declared by client — Phase 1 verifies these
    declared_modality: Literal["tabular","cv","nlp","time_series","llm","agentic","gpai"]
    declared_risk_tier: Literal["high","limited","minimal","gpai"]  # client self-assessment
    declared_annex_iii_sections: list[Literal["1","2","3","4","5","6","7","8"]]
    deployment_context: Literal["b2b","b2c","public_sector","internal"]
    provider_elects_third_party: bool   # Art. 43 §1(b)
    gdpr_overlap: bool                  # triggers Privacy Tier-3
    gpai_general_purpose: bool          # triggers Arts. 51–55 module
    special_category_data: bool         # Art. 10 + Privacy Tier-3
    # preview Art. 43 decision derived from declared values (§3.5)
    art43_preview: str | None           # written by art43_select at Stage A submission
    cgsa_assessment_id: str | None      # links to upstream S4 CGSA run if available

class AnnexIVDossier(TypedDict):
    """Annex IV §1–§9 technical documentation uploaded in Stage B."""
    # §1 General description
    general_description: str
    model_type: str                     # e.g. "XGBoost classifier v1.2"
    # §2 Design and development
    design_process: str
    training_data_description: str
    data_governance_measures: str
    # §3 Monitoring, functioning, and control
    monitoring_measures: str
    logging_capabilities: str
    # §4 Performance metrics
    accuracy_metrics: dict[str, float]  # e.g. {"accuracy": 0.92, "f1": 0.88}
    robustness_metrics: dict[str, float] | None
    # §5 Risk management (Art. 9)
    risk_management_file_uri: str | None   # MinIO URI to PDF/DOCX
    # §6 Lifecycle changes
    lifecycle_change_log: list[str]
    # §7 Standards applied
    harmonised_standards: list[str]
    other_standards: list[str]
    # §8 EU declaration of conformity (if self-assessment route)
    eu_doc_uri: str | None
    # §9 Post-market monitoring plan
    post_market_plan_uri: str | None
    # L-branch additional fields (populated only when declared_modality ∈ {llm, agentic, gpai})
    system_prompt_uri: str | None
    rag_manifest_uri: str | None        # vector-store schema + retrieval config
    tool_inventory: list[str] | None    # tool names + permitted scopes
    guardrail_config_uri: str | None
    golden_set_uri: str | None          # Q&A pairs for RAGAs eval

class StageCAccess(TypedDict):
    """Scoped live-system access credentials granted in Stage C (§11, §6 Stage 0)."""
    read_only_api_endpoint: str | None     # read-only inference endpoint for Phase 1–4
    credential_ref: str                    # OpenBao secret path — never inlined
    access_scope: list[str]               # e.g. ["inference", "logprobs", "metadata"]
    access_expiry_utc: str                 # ISO-8601; must expire ≤ engagement_end_date
    revocation_webhook: str | None         # client webhook called on engagement close

class ClientSubmission(TypedDict):
    """Root intake bundle — union of Stage A + B + C artefacts."""
    stage_a: StageATriage
    stage_b: AnnexIVDossier
    stage_c: StageCAccess | None        # None for offline / demo mode
    intake_completeness_score: float    # §9.1 KPI 0; written by T01c; must be ≥ 0.80

# ──────────────────────────────────────────────────────────────────────────────
# AuditState — full LangGraph typed dict threaded through the graph
# ──────────────────────────────────────────────────────────────────────────────
class AuditState(TypedDict):
    # --- engagement identity ---
    engagement_id: str
    client_submission: ClientSubmission  # full three-stage intake bundle

    # --- declared values (from Stage A — immutable after Stage A close) ---
    declared_modality: Literal["tabular","cv","nlp","time_series","llm","agentic","gpai"]
    declared_risk_tier: Literal["high","limited","minimal","gpai"]
    declared_annex_iii_sections: list[Literal["1","2","3","4","5","6","7","8"]]

    # --- Phase 1 verified values (may differ from declared) ---
    risk_tier: Literal["prohibited","high","limited","minimal","gpai"]
    annex_iii_mapping: list[AnnexIIIEntry]           # §3.6 — carries provenance field
    modality: Literal["tabular","cv","nlp","time_series","llm","agentic","gpai"]
    deployment_context: Literal["b2b","b2c","public_sector","internal"]
    is_llm_or_agentic: bool                          # Router decision (from declared; overridable)
    provider_elects_third_party: bool                # from Stage A; confirmed by Phase 1
    harmonised_standards_applied: bool               # set by Phase 5 from CGSA

    # --- declared-vs-verified diff (written by declaration_diff tool after Phase 1) ---
    declaration_verification: dict[str, Literal[
        "match",          # Phase 1 confirms declared value
        "mismatch",       # Phase 1 finds a different value → HITL trigger
        "corrected",      # Phase 1 adjusts section/tier; documents rationale
        "not_verifiable"  # insufficient evidence to confirm or refute
    ]]                                               # key = field name, value = verdict

    # --- Article 43 (§3.5) ---
    art43_decision: Art43Decision | None             # final (verified) decision; preview in T01a

    # --- artefact graph ---
    phase_artefacts: dict[str, ArtefactRef]          # template_id -> Evidence Store URI

    # --- S4 CGSA hand-off (full surface; §5.4 map) ---
    cgsa_payload: CGSAPayload | None                 # parsed + schema-validated S4 JSON
    cgsa_schema_version: str | None                  # pinned (e.g. "1.0.0")
    cgsa_composite_maturity_score: float | None      # 0.0–4.0
    cgsa_composite_maturity_label: str | None        # absent | initial | developing | defined | optimised
    cgsa_eu_ai_act_coverage_pct: float | None        # 0.0–100.0
    cgsa_csp_satisfiable: bool | None
    cgsa_governance_verdict: Literal["compliant","partially_compliant","non_compliant"] | None
    cgsa_phase5_verdict: Literal["PASS","PASS_WITH_OBSERVATIONS","FAIL"] | None
    cgsa_phase5_narrative: str | None                # pre-written summary
    cgsa_blocking_findings: list[BlockingFinding]
    cgsa_positive_findings: list[PositiveFinding]
    cgsa_low_confidence_controls: list[LowConfidenceControl]   # confidence < 0.6 → HITL flag
    cgsa_recommended_follow_up: list[FollowUpItem]
    cgsa_report_url: str | None                      # hyperlinked in Phase 6 report
    cgsa_risk_tier_match: bool | None                # Phase 1 verified tier vs CGSA metadata

    # --- compliance assembly ---
    compliance_matrix: dict[Article, Verdict]        # Art. 9, 10, 11, 13, 14, 15, 17, 43; Annex III/IV; GPAI 51–55
    blocking_findings: list[Finding]
    positive_findings: list[Finding]
    remediation_roadmap: list[RemediationItem]

    # --- verification & verdict ---
    verifier_critiques: dict[str, Critique]
    intake_completeness_score: float | None          # §9.1 KPI 0; 0.0–1.0; must be ≥ 0.80
    completeness_score: float | None                 # §9.1 KPI 1; 0.0–1.0
    regulatory_coverage_pct: float | None            # §9.1 KPI 2; 0.0–100.0
    final_verdict: Literal["PASS","PASS_WITH_OBSERVATIONS","FAIL"] | None
```

### 5.2 Evidence Store

Following Anthropic's pattern of writing intermediate work to the filesystem to avoid context-window blow-up:

- **Object store**: MinIO (S3-wire-compatible, AGPL-v3) — same binary in dev and prod, with SOC-2 controls applied at the deployment layer.
- **Index**: Postgres table `evidence(engagement_id, phase, artefact_type, uri, sha256, created_at, created_by_agent)`.
- **Access**: Agents receive *URIs and summaries*, not blobs. Only the Verifier and Phase 6 Report Architect pull full artefacts.

### 5.3 Inter-Agent Messaging

Four message types only (kept minimal per Anthropic's lesson on prompt-budget discipline):

| Message | Direction | Payload |
|---------|-----------|---------|
| `IntakeDispatch` | Orchestrator → Intake Validator | `{engagement_id, stage_a_uri, stage_b_uri, stage_c_uri, annex_iv_schema_version}` |
| `Dispatch` | Orchestrator → Phase Agent | `{phase_id, task_brief, evidence_uris, output_contract, declaration_summary}` |
| `Report` | Phase Agent → Orchestrator | `{phase_id, artefact_uri, summary, confidence, tool_calls, declaration_verification_delta}` |
| `Critique` | Verifier → Orchestrator | `{phase_id, verdict, issues[], rerun_required: bool}` |

**`declaration_summary`** in every Dispatch brief is a compact JSON derived from `AuditState.declared_*` fields so phase agents know the client-stated modality, risk tier, and Annex III sections without pulling the full intake bundle. Phase 1 additionally receives `T01a_stage_a_triage` and `T01b_annex_iv_dossier` URIs so it can perform the verification step.

**`declaration_verification_delta`** in every Report carries any field where the agent found a discrepancy with the declared values; the Orchestrator merges these deltas into `AuditState.declaration_verification`.

There is **no peer-to-peer chatter** between phase agents. All coordination flows through the Orchestrator — the same hub-and-spoke topology Anthropic chose to keep debugging tractable.

### 5.4 S4 CGSA Payload Consumption Map

The S4 `uagf_cgsa_aaa_schema.json` (schema_version `1.0.0`, draft-07) is the canonical input to Phase 5. Every required and optional field is consumed; nothing is dropped. The table below is the **binding contract** between S4 and S5 and matches the schema joint-meeting agreement (exposé Week 4).

| S4 schema path | Type | AAA destination | AAA usage |
|---|---|---|---|
| `metadata.assessment_id` | uuid | `cgsa_payload.metadata.assessment_id` | Dedup key; trace ID emitted on the Phase 5 span |
| `metadata.organisation_name` | string | T17 compliance matrix header; T18 cover page | Report identification |
| `metadata.system_under_audit` | string | T18 cover page | Report identification |
| `metadata.cgsa_version` | semver | `cgsa_payload.metadata.cgsa_version` | Pinned-version assertion in Phase 5; mismatch ⇒ Verifier `escalate_hitl` |
| `metadata.assessment_timestamp` | ISO-8601 | T14 footer | Provenance |
| `metadata.risk_tier` | enum | Cross-check vs Phase 1 `risk_tier`; sets `cgsa_risk_tier_match` | If mismatch ⇒ HITL trigger (§8.4) |
| `metadata.document_sources[]` | string[] | T14 "Source documents" section | Cited in Phase 5 narrative |
| `metadata.uagf_gmm_version` | semver | T14 footer | Reproducibility |
| `overall_scores.composite_maturity_score` | 0.0–4.0 | `cgsa_composite_maturity_score`; T17 row "Governance maturity" | Executive-summary KPI |
| `overall_scores.composite_maturity_label` | enum | T17 row "Governance maturity" | Human-readable label |
| `overall_scores.eu_ai_act_coverage_pct` | 0.0–100.0 | `cgsa_eu_ai_act_coverage_pct`; T17 row "EU AI Act coverage" | Threshold 80% gate for PASS vs PASS_WITH_OBS |
| `overall_scores.csp_satisfiable` | bool | `cgsa_csp_satisfiable` | Binary gate; `false` ⇒ Phase 5 verdict FAIL |
| `overall_scores.governance_verdict` | enum | `cgsa_governance_verdict` | T14 header chip |
| `overall_scores.controls_assessed / meeting / below_threshold` | int | T14 gap summary table | Verbatim |
| `domains[]` (6 fixed: D1–D6) | array | T14 "Findings by domain" sub-table (one row per domain) | Iterated; each row shows `domain_score`, `domain_eu_ai_act_articles` |
| `domains[].controls[].control_id / name / maturity_score / maturity_label` | — | T14 control table | Verbatim |
| `domains[].controls[].source_frameworks[]` (12 frameworks) | enum[] | Regulatory RAG corpus assertion: index must contain at least these 12 | If any framework is missing from RAG index ⇒ build-time CI failure |
| `domains[].controls[].evidence_summary / evidence_source_document / evidence_page_reference` | string | T14 "Evidence" column | Quoted with source citation |
| `domains[].controls[].confidence` | 0.0–1.0 | If `< 0.6` ⇒ append to `cgsa_low_confidence_controls` | Phase 5 limitations section + HITL flag |
| `domains[].controls[].eu_ai_act_articles[]` | string[] | T17 compliance matrix cell `(article, control_id)` | Drives article-coverage calculation |
| `domains[].controls[].hard_constraint.{applicable,threshold_score,satisfied,eu_ai_act_obligation}` | object | T14 + T17 hard-constraint indicator | `satisfied=false` ⇒ blocking finding |
| `domains[].controls[].gap_severity` | enum or null | T14 severity column | Sort key for findings list |
| `domains[].controls[].gap_detail` | string | T14 "Gap" column; T18 remediation narrative | Verbatim |
| `eu_ai_act_compliance_matrix.article_{9,10,13}` | object (required) | T17 rows Art. 9, 10, 13 | Status + coverage_pct + violated controls |
| `eu_ai_act_compliance_matrix.article_{14,17}` | object (optional) | T17 rows Art. 14, 17 (marked "informational") | Same |
| `hard_constraint_results.csp_satisfiable / total_hard_constraints / violated_constraints[] / satisfied_constraints[]` | object | T14 "Hard constraint summary" + T17 violated cells | Sorted by `score_delta` |
| `remediation_roadmap[]` | array | T18 §"Remediation roadmap" | Verbatim, sorted by `rank`; items with `gap_severity=critical` mirrored to T17 blocking findings |
| `aaa_phase5_handoff.phase5_verdict` | enum | `cgsa_phase5_verdict`; T14 traffic-light + T18 exec-summary chip | Primary Phase 5 verdict (overrides locally computed) |
| `aaa_phase5_handoff.phase5_narrative_summary` | string (3–5 sentences) | `cgsa_phase5_narrative`; T14 narrative paragraph | Inserted into Phase 5 with light editorial pass only |
| `aaa_phase5_handoff.blocking_findings_count` | int | T14 header KPI badge | "N blocking findings" |
| `aaa_phase5_handoff.blocking_findings[]` | array | `cgsa_blocking_findings`; T14 critical-findings table | One row per item |
| `aaa_phase5_handoff.positive_findings[]` | array | `cgsa_positive_findings`; T14 positive-findings table | One row per item |
| `aaa_phase5_handoff.low_confidence_controls[]` | array | `cgsa_low_confidence_controls`; T14 "Limitations" + HITL flag per item | Every entry must produce a Phase 5 limitations bullet |
| `aaa_phase5_handoff.aaa_recommended_follow_up[]` | array | `cgsa_recommended_follow_up`; T14 "Follow-up" section | Items with `urgency = required_before_report_completion` **block** Phase 6 until either fulfilled or HITL-overridden |
| `aaa_phase5_handoff.cgsa_report_url` | uri or null | T14 "Full governance report" hyperlink in T18 | Direct link in PDF if present |

**Validation contract.** On Phase 5 entry, `cgsa_ingest` runs `schema_validate(payload, schema_version="1.0.0")`. Any validation failure halts Phase 5 with verdict `escalate_hitl`. Schema-version drift (S4 ships a newer schema than AAA pins) is treated as a deploy-blocking incident: CI runs a contract test on every push that lints the pinned schema against the live S4 repo (`github.com/UAGF/cgsa-aaa-schema`).

---

## 6. End-to-End Workflow (Reference Run)

The canonical execution graph, expressed as a LangGraph-style state machine, has **twelve logical stages** (Stage 0 is now three sub-stages; Stages 4a–4c run in parallel when the Router selects the standard branch; stage 4L replaces them on the L-branch).

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  0. STAGE 0 — INTAKE (three mandatory sub-stages before any agent runs)      │
│                                                                              │
│  0A · Stage A — Triage                                                       │
│       Client fills ~20-question form in Next.js wizard / Streamlit demo.     │
│       Declares: modality, risk tier, Annex III sections, deployment context, │
│       provider_elects_third_party, GDPR overlap, GPAI flag, CGSA ID.        │
│       art43_preview computed from declared values → written to T01a.         │
│       Completeness gate: if required Stage A fields missing → wizard blocks. │
│                                                                              │
│  0B · Stage B — Annex IV Dossier Upload                                      │
│       Client uploads Annex IV §1–§9 technical documentation (structured      │
│       form + file attachments). L-branch clients additionally upload:        │
│       system prompt, RAG manifest, tool inventory, guardrail config,         │
│       golden set (Q&A pairs for RAGAs eval).                                 │
│       annex_iv_validator runs JSON-Schema check on submission.               │
│       intake_completeness_calculator writes T01c with intake_completeness_  │
│       score. Gate: intake_completeness_score ≥ 0.80 required to proceed.    │
│       If score < 0.80 → wizard returns error list; client must remediate.    │
│                                                                              │
│  0C · Stage C — Scoped Live-System Access (optional, async)                  │
│       Client provides read-only API endpoint + scoped credentials via the    │
│       portal's secure vault form. Credentials stored in OpenBao; only a     │
│       secret-path reference is written to AuditState. Access scope and       │
│       expiry are constrained by the platform (§11).                          │
│       If absent (offline/demo mode): Phase 1 marks live-system evidence      │
│       as "not_verifiable" in declaration_verification map.                   │
│                                                                              │
│  Orchestrator instantiates AuditState, writes T01a/T01b/T01c to Evidence.   │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  1. PLAN (Orchestrator + csp_solver)                                         │
│     Runs python-constraint over (declared_risk_tier, declared_modality,      │
│     deployment_context) to produce a PREVIEW plan written to T01a.           │
│     Final plan is recomputed after Phase 1 against verified values.          │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  2. PHASE 1 — SCOPE (Declaration Verifier Agent)                             │
│     - Receives T01a + T01b URIs; reads declared values                       │
│     - Verifies declared modality, risk tier, Annex III sections against      │
│       intake-bundle evidence + Regulatory RAG corpus                         │
│     - Emits declaration_verification map via declaration_diff tool           │
│     - Art. 5 prohibition gate  ─── if violated → HALT, escalate to HITL      │
│     - GPAI screening                                                         │
│     - Confirms is_llm_or_agentic (overrides declared value only if mismatch) │
│     - Declaration mismatch (any field = "mismatch") → HITL trigger (§8.4)   │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                          ┌───────┴────────┐  Router
                          ▼                ▼
                    standard branch    L-branch
                          │                │
   ┌──────────────────────┼──────────┐     │
   ▼                      ▼          ▼     ▼
┌──────────┐      ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐
│ 4a Phase2│      │ 4b Phase3│  │ 4c Phase4│  │ 4L UAGF-TAM-L Agent     │
│ Data     │      │ Model    │  │ Output   │  │ (replaces Phases 2–4)   │
│ Auditor  │      │ Validator│  │ Fairness │  │ RAGAs + injection +     │
│ (par.)   │      │ (par.)   │  │ (par.)   │  │ trajectory audit        │
└──────────┘      └──────────┘  └──────────┘  └─────────────────────────┘
   │                  │              │                    │
   └──────────────────┴──────────────┴────────────────────┘
                                  │
                                  ▼  (each phase output gated by Verifier)
┌──────────────────────────────────────────────────────────────────────────────┐
│  5. PHASE 5 — GOVERNANCE (Governance Agent)                                  │
│     - cgsa_ingest(uagf_cgsa_aaa_schema.json) from upstream S4                │
│     - schema_validate                                                        │
│     - Cross-checks Phase 1 risk_tier vs metadata.risk_tier                   │
│     - Lifts aaa_phase5_handoff.{blocking_findings, positive_findings,        │
│       remediation_roadmap, phase5_verdict} into AuditState                   │
│     - Spawns Tier-3 specialists (Cyber, Privacy) if Art. 15 / GDPR gaps     │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  6. COMPLIANCE MATRIX ASSEMBLY (Orchestrator)                                │
│     - Runs art43_select (§3.5) → writes T05_art43_decision                   │
│     - For each Article in {9, 10, 13, 14, 15, 17, 43; Annex III;             │
│       GPAI 51–55}: verdict = f(phase_artefacts, cgsa_payload, critiques)     │
│     - Computes completeness_score and regulatory_coverage_pct (§9.1)         │
│     - Final verdict = conjunction(Art.5 pass, csp_satisfiable,               │
│                                   phase5_verdict ∈ {PASS, PASS_W_OBS},       │
│                                   all required_before_report_completion      │
│                                   follow-ups satisfied)                      │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  7. HITL CHECKPOINT (optional, configurable)                                 │
│     If final_verdict = FAIL or risk_tier = high: human reviewer notified;    │
│     audit pauses until sign-off or override.                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  8. PHASE 6 — REPORT (Report Architect Agent)                                │
│     report_render() → Annex IV-aligned PDF + machine-readable JSON           │
│     Delivered to client portal; signed with engagement key.                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Workflow Diagram

```mermaid
flowchart TD
    classDef intake fill:#e8eef9,stroke:#3b5998,color:#0b1f44
    classDef orch fill:#5b6cff,stroke:#2a3aad,color:#ffffff
    classDef phase fill:#7fb069,stroke:#3f6a32,color:#0b1f08
    classDef branch fill:#f4c95d,stroke:#8a6a14,color:#2a1f06
    classDef gate fill:#e07a5f,stroke:#8b3a23,color:#ffffff
    classDef report fill:#9b8acb,stroke:#4d3a87,color:#ffffff
    classDef store fill:#cfd8dc,stroke:#546e7a,color:#0b1f08

    SA[/"0A · Stage A · Triage<br/>~20-question form · declared modality/risk/Annex III<br/>→ T01a · art43_preview"/]:::intake
    GATECS{"completeness<br/>≥ 0.80?"}:::gate
    SB[/"0B · Stage B · Annex IV Dossier<br/>§1–§9 upload · annex_iv_validator<br/>→ T01b · T01c (intake_completeness_score)"/]:::intake
    SC[/"0C · Stage C · Scoped Access<br/>read-only API creds → OpenBao vault<br/>(optional; absent = not_verifiable)"/]:::intake
    S1["1 · Plan<br/>Orchestrator + csp_solver<br/>(preview plan from declared values)"]:::orch
    S2["2 · Phase 1 · Scope<br/>Declaration Verifier · Sonnet<br/>declaration_diff → declaration_verification"]:::phase
    GATEDECL{"declaration<br/>mismatch?"}:::gate
    GATE5{"Art. 5<br/>prohibition?"}:::gate
    ROUTER{"Router<br/>is_llm_or_agentic?"}:::orch

    P2["4a · Phase 2 · Data<br/>Auditor · Sonnet"]:::phase
    P3["4b · Phase 3 · Model<br/>Validator · Opus"]:::phase
    P4["4c · Phase 4 · Output<br/>Fairness · Sonnet"]:::phase
    PL["4L · UAGF-TAM-L<br/>Branch · Opus"]:::branch

    VER{{"Verifier · Opus<br/>(per-phase critic)"}}:::orch

    P5["5 · Phase 5 · Governance · Opus<br/>cgsa_ingest(uagf_cgsa_aaa_schema.json)"]:::phase
    SPEC["Spawn Tier-3<br/>Cyber · Sonnet / Privacy · Sonnet"]:::branch

    MATRIX["6 · Compliance Matrix<br/>Orchestrator · Opus<br/>art43_select (final) · intake_completeness_score"]:::orch
    HITL{"7 · HITL<br/>checkpoint?"}:::gate
    REPORT["8 · Phase 6 · Report Architect · Sonnet<br/>Annex IV PDF + JSON"]:::report

    HALT[/"HALT · escalate to HITL"/]:::gate
    EVID[("Evidence Store<br/>MinIO + Postgres")]:::store

    SA --> SB --> GATECS
    GATECS -- "< 0.80 → remediate" --> SB
    GATECS -- "≥ 0.80" --> SC --> S1 --> S2
    S2 --> GATEDECL
    GATEDECL -- mismatch --> HALT
    GATEDECL -- ok --> GATE5
    GATE5 -- yes --> HALT
    GATE5 -- no --> ROUTER
    ROUTER -- standard --> P2 & P3 & P4
    ROUTER -- L-branch --> PL
    P2 --> VER
    P3 --> VER
    P4 --> VER
    PL --> VER
    VER -- accept --> P5
    VER -- rerun --> P2
    VER -- escalate --> HALT
    P5 -. on demand .-> SPEC
    SPEC --> P5
    P5 --> MATRIX --> HITL
    HITL -- pass / approved --> REPORT
    HITL -- needs review --> HALT

    SA -. T01a .-> EVID
    SB -. T01b · T01c .-> EVID
    S2 -. T02 · declaration_verification .-> EVID
    P2 -. artefacts .-> EVID
    P3 -. artefacts .-> EVID
    P4 -. artefacts .-> EVID
    PL -. artefacts .-> EVID
    P5 -. CGSA payload .-> EVID
    REPORT -. signed report .-> EVID
```

### 6.2 Risk-Tier × Phase Constraint Catalogue

The `csp_solver` tool (§4.5) runs the catalogue below at Plan time (Stage 1) to decide, for each engagement, which phases are **mandatory**, which are **optional**, and which are **skipped**. The catalogue is the executable form of the exposé Week-12 rule "*if risk tier = minimal → skip Phases 3/4 → Ops + Report; if risk tier = high → all 6 phases in full*". It is owned by the Orchestrator and version-pinned per audit so a regulator can replay the routing decision.

**Decision variables** — the CSP runs twice per engagement: (i) **preview plan** at the end of Stage A against declared values; (ii) **final plan** after Phase 1 against verified values. The table below marks which source applies at each run.

| Variable | Domain | Source — preview plan | Source — final plan |
|---|---|---|---|
| `risk_tier` | {prohibited, high, limited, minimal, gpai} | `declared_risk_tier` (Stage A) | Phase 1 verified |
| `modality` | {tabular, cv, nlp, time_series, llm, agentic, gpai} | `declared_modality` (Stage A) | Phase 1 verified |
| `is_llm_or_agentic` | {true, false} | derived from `declared_modality` | Phase 1 confirmed/overridden |
| `annex_iii_section` | {none, 1, 2, …, 8} | `declared_annex_iii_sections` (Stage A) | Phase 1 verified (§3.6) |
| `special_category_data` | {true, false} | Stage A declaration | Phase 2 PII scan (final) |
| `provider_elects_third_party` | {true, false} | Stage A Triage form | Stage A (immutable) |
| `intake_completeness_score` | 0.0–1.0 | T01c (end of Stage B) | unchanged — immutable |

**Phase-status catalogue** (M = mandatory, O = optional, S = skip):

| Risk tier | Modality | P1 Scope | P2 Data | P3 Model | P4 Output | P5 Gov/Ops | P6 Report | UAGF-TAM-L | Cyber spawn | Privacy spawn |
|---|---|---|---|---|---|---|---|---|---|---|
| **prohibited** | any | M | S | S | S | S | M (HALT report only) | S | S | S |
| **high** | tabular | M | M | M | M | M | M | S | O (Art.15) | M (if special-cat) |
| **high** | cv | M | M | M | M | M | M | S | **M** (Art.15) | M (if Annex III §1) |
| **high** | nlp | M | M | M | M | M | M | S | O | M (PII) |
| **high** | time_series | M | M | M | O (limited) | M | M | S | O | S |
| **high** | llm / agentic | M | M (provenance only) | S | S | M | M | **M** (replaces P2–P4) | **M** | O |
| **limited** | tabular / cv / nlp / time_series | M | M | O | O | M | M | S | S | O (if PII) |
| **limited** | llm / agentic | M | O | S | S | M | M | **M** | O | O |
| **minimal** | any (non-LLM) | M | O | S | S | **M (Ops only)** | M | S | S | S |
| **minimal** | llm / agentic | M | O | S | S | M | M | O (golden set only) | S | S |
| **gpai** | llm / agentic | M | O | S | S | M | M (+ Arts. 51–55) | **M** | M | O |

**Hard constraints** the CSP enforces in addition to the table:

1. `is_llm_or_agentic = true` ⇒ UAGF-TAM-L = M, P3 = S, P4 = S (exposé Week-12 routing).
2. `annex_iii_section = 1` (biometrics) ⇒ Cyber = M, Privacy = M, `art43_select` ⇒ Annex VII unless harmonised standards fully applied.
3. `special_category_data = true` ⇒ Privacy = M.
4. `risk_tier = high` ⇒ P5 = M and CGSA payload required before Phase 6 can run.
5. `risk_tier = prohibited` ⇒ workflow HALTs after Phase 1, report contains only T01a–T05.
6. `cgsa_recommended_follow_up[*].urgency = required_before_report_completion` ⇒ Phase 6 blocked until each follow-up is resolved or HITL-overridden.
7. `intake_completeness_score < 0.80` ⇒ Phase 1 **cannot start**; the engagement is blocked at Stage B with a remediation list (enforced by `annex_iv_validator` at intake close, not by the CSP solver).
8. Any `declaration_verification[field] = "mismatch"` after Phase 1 ⇒ HITL trigger raised before the final CSP plan is accepted; if human reviewer overrides, the mismatch is logged in T01c and T02 with override rationale.
9. `declared_modality ≠ modality` (Phase 1 correction) ⇒ CSP must be rerun with the corrected modality before Phase 2 can start.

**Python encoding** (reference implementation):

```python
from constraint import Problem

def build_phase_csp(state: AuditState) -> Problem:
    p = Problem()
    p.addVariables(["P1","P2","P3","P4","P5","P6","L","CYBER","PRIV"], ["M","O","S"])
    # rule 1
    p.addConstraint(lambda p1: p1 == "M", ["P1"])
    p.addConstraint(lambda p6: p6 == "M", ["P6"])
    if state["risk_tier"] == "prohibited":
        for v in ("P2","P3","P4","P5","L","CYBER","PRIV"):
            p.addConstraint(lambda x, _v=v: x == "S", [v])
    if state["is_llm_or_agentic"]:
        p.addConstraint(lambda l: l == "M", ["L"])
        p.addConstraint(lambda p3: p3 == "S", ["P3"])
        p.addConstraint(lambda p4: p4 == "S", ["P4"])
    if state["risk_tier"] == "high":
        p.addConstraint(lambda p5: p5 == "M", ["P5"])
    if any(e["annex_iii_section"] == "1" for e in state["annex_iii_mapping"]):
        p.addConstraint(lambda c: c == "M", ["CYBER"])
        p.addConstraint(lambda pr: pr == "M", ["PRIV"])
    if state.get("special_category_data"):
        p.addConstraint(lambda pr: pr == "M", ["PRIV"])
    return p
```

The solver returns the unique satisfying assignment; if no assignment exists (over-constrained engagement), the Orchestrator escalates to HITL with the conflict trace.

---

## 7. Per-Archetype Execution Paths

The Router (Phase 1 output) and Orchestrator plan together select which subset of agents and tools is invoked. Seven archetypes are supported on day one. The **Intake artefacts required** column lists the Stage B Annex IV §sections that must be present (score ≥ 0.80) for that archetype.

| Archetype | Router decision | Phase agents invoked | Tools heavily used | Tier-3 spawns (typical) | Intake artefacts required (Stage B) |
|-----------|-----------------|----------------------|--------------------|--------------------------|--------------------------------------|
| **Tabular classifier** (credit, hiring) | standard | 1,2,3,4,5,6 | data_profile, shap_explain, demographic_parity, disparate_impact | Privacy (if special-category) | Annex IV §1–§5, §7; training dataset card (T06); risk-management file (Art. 9); accuracy + fairness metrics |
| **Computer-vision classifier** (medical imaging, biometric) | standard | 1,2,3,4,5,6 | gradcam_explain, robustness_probe, subgroup_metrics | Cyber, Privacy (biometric) | Annex IV §1–§5, §7; robustness metrics; Annex III §1 declaration; Cyber contact |
| **Time-series / forecasting** | standard | 1,2,3,5,6 (Phase 4 limited) | drift_test, metric_suite | — | Annex IV §1–§4, §7; drift-monitoring plan; SLA thresholds |
| **NLP classifier** (sentiment, toxicity) | standard | 1,2,3,4,5,6 | lime_explain, toxicity_classifier, subgroup_metrics | Privacy (PII) | Annex IV §1–§5, §7; training corpus card; PII processing declaration |
| **LLM (chat / RAG)** | L-branch | 1, **L**, 5, 6 | ragas_eval, groundedness_check, prompt_injection_suite | Cyber | Annex IV §1–§5, §7–§9; **system prompt** (URI); **RAG manifest**; guardrail config; golden set ≥ 50 Q&A pairs; GPAI arts. declared if applicable |
| **Agentic system** (tool-using) | L-branch | 1, **L**, 5, 6 | trajectory_audit, prompt_injection_suite | Cyber | Annex IV §1–§5, §7–§9; system prompt; **tool inventory** (names + permitted scopes); Langfuse trace sample; guardrail config |
| **GPAI foundation model** | L-branch + GPAI flag | 1, **L**, 5, 6 (Art. 51–55 matrix) | ragas_eval, prompt_injection_suite, regulatory_search | Cyber, Privacy | Annex IV §1–§9 (all sections); model architecture description; training data summary (scale + diversity); GPAI §51–§55 self-assessment; red-team report |

---

## 8. Reliability, Error Handling & HITL

Anthropic's lesson — *"agents are stateful, errors compound"* — drives a four-layer reliability strategy.

### 8.1 Per-Tool Retry Policy

| Failure type | Strategy |
|--------------|----------|
| Transient (timeout, 5xx) | Exponential back-off, max 3 attempts |
| Schema-validation failure | Re-prompt agent with the validation error appended |
| Tool returns empty / degenerate result | Mark artefact `inconclusive`, escalate to Verifier |
| LLM refusal / safety filter | Switch to fallback model, log incident |

### 8.2 Verifier Loop

Every phase artefact passes through the Verifier before the Orchestrator accepts it. The Verifier returns one of:

- `accept` — artefact admitted to state
- `accept_with_notes` — admitted; notes appended to compliance matrix
- `rerun` — phase agent re-invoked with the critique as additional context (max 2 reruns)
- `escalate_hitl` — paused for human review

### 8.3 Checkpointing

`AuditState` is checkpointed to Postgres after every successful stage transition (LangGraph `PostgresSaver`). This allows:
- Resume after crash without re-running expensive phases
- Time-travel debugging (replay any state)
- Deterministic re-runs for regulator inspection

### 8.4 Human-in-the-Loop Triggers

| Trigger | When raised | Action |
|---------|-------------|--------|
| **Intake completeness below threshold** | End of Stage B: `intake_completeness_score < 0.80` | Wizard returns field-level remediation list to client; no HITL agent needed. If client disputes a required field, senior reviewer may lower threshold per engagement with written rationale (logged in T01c). |
| **Declaration mismatch** | After Phase 1 `declaration_diff` run: any `declaration_verification[field] = "mismatch"` | Reviewer is notified with the specific field, declared value, Phase-1 verified value, and evidence citations. Reviewer either (a) accepts Phase 1 correction → CSP reruns; (b) accepts client declaration → Phase 1 result overridden with documented rationale. |
| Art. 5 prohibition tripped | Phase 1 gate | Hard halt; senior reviewer must sign override or engagement is terminated. |
| Risk tier = high AND final_verdict ∈ {FAIL, PASS_W_OBS} | Phase 6 complete | Reviewer notified; client portal flag raised before report is delivered. |
| Verifier escalates after 2 reruns | Per-phase verification loop | Reviewer adjudicates the artefact; may accept or request Phase agent re-invocation with amended brief. |
| `csp_satisfiable = false` from upstream S4 | Phase 5 CGSA ingest | Reviewer reconciles Phase 1 verified tier vs CGSA metadata mismatch. |
| Cyber Sub-Agent finds active exploit | Phase 5 or Tier-3 Cyber run | Immediate notification + report freeze; engagement paused until client confirms remediation. |
| Preview vs final Art. 43 decision differ | After Phase 1 (§3.5) | Reviewer informed; the delta is recorded in T01c and T02; client notified via portal. |

HITL reviewers act *only* on flagged checkpoints; they do not micro-manage agents. This preserves the autonomy promise while keeping the firm legally defensible. All HITL decisions (action taken + rationale) are appended to the `evidence` Postgres table as `hitl_decision` artefact type so the engagement audit trail is complete.

---

## 9. Evaluation & Observability

Following dev.to ("governance from the start"), Anthropic's emphasis on rigorous eval, and Koshiyama 2022's call for standardised audit-completeness measurement.

### 9.1 Four-Tier Evaluation

| Tier | What is measured | Method | Frequency |
|------|------------------|--------|-----------|
| **Per-tool** | Determinism, schema conformance | Unit tests on golden inputs | CI on every change |
| **Per-agent** | Task success, citation accuracy, hallucination rate | LLM-as-judge (independent model) + golden traces | Nightly + on prompt change |
| **Per-engagement KPIs** | Intake completeness, artefact completeness, regulatory coverage % | Deterministic rubric (below) | Every engagement, written to T01c + T17 + T18 |
| **End-to-end** | Final verdict vs human-expert verdict on the 4 thesis case studies | Confusion matrix on PASS/FAIL/PASS_W_OBS + KPI deltas | Once per case study; supervisor review per exposé M5 |

**Primary KPIs — exposé Sub-Q 3.** Three KPIs are computed deterministically and embedded in T01c (KPI 0), T17, and T18 (KPIs 1 and 2).

#### KPI 0 — Intake Completeness Score (`intake_completeness_score`, 0.0–1.0)

> *Fraction of required Annex IV §1–§9 fields (weighted by section) that are present, non-empty, and schema-valid in the Stage B dossier (T01b).*

```python
def intake_completeness_score(submission: ClientSubmission) -> float:
    """Computed by intake_completeness_calculator at Stage B close.
    Written to T01c and AuditState.client_submission.intake_completeness_score.
    Must be >= 0.80 for Phase 1 to start (§6.2 constraint 7)."""
    section_weights = {1: 0.20, 2: 0.15, 3: 0.10, 4: 0.15,
                       5: 0.15, 6: 0.05, 7: 0.10, 8: 0.05, 9: 0.05}
    score = 0.0
    for section, weight in section_weights.items():
        completeness = _section_completeness(submission["stage_b"], section)
        score += weight * completeness
    return round(score, 2)
```

Conditional fields (e.g. L-branch golden set) are only required when `declared_modality ∈ {llm, agentic, gpai}`. Missing a conditional field when not applicable does not reduce the score. The gate threshold (0.80) is configurable per rubric version; any change requires supervisor sign-off and a new semver tag on `uagf-tam-templates`.

#### KPI 1 — Completeness Score (`completeness_score`, 0.0–1.0)

> *Fraction of the 20 expected artefact templates that are present, schema-valid, and admitted by the Verifier for the given engagement.*

```python
def completeness_score(state: AuditState) -> float:
    csp = state["phase_status"]                      # output of §6.2 CSP
    expected = {tid for tid, status in csp.items() if status in {"M","O"}}
    delivered = {tid for tid, ref in state["phase_artefacts"].items()
                 if state["verifier_critiques"][tid]["verdict"] in {"accept","accept_with_notes"}}
    return len(delivered & expected) / max(len(expected), 1)
```

Mandatory templates have weight 1.0; optional templates have weight 0.5 (configurable per rubric version). The score is reported to two decimal places and benchmarked against the human-expert audit on each case study (exposé M5).

#### KPI 2 — Regulatory Coverage % (`regulatory_coverage_pct`, 0.0–100.0)

> *Fraction of the in-scope EU AI Act articles for which the audit produces at least one admitted evidence artefact with a verifiable RAG-cited regulatory clause.*

In-scope article set depends on `risk_tier`:

| Risk tier | In-scope articles |
|---|---|
| high (standard) | Art. 9, 10, 13, 14, 15, 17, 43; Annex III; Annex IV |
| high (LLM/agentic) | Art. 9, 10, 13, 14, 15, 17, 43; Annex III; GPAI 51–55 |
| limited | Art. 13, 50 (transparency); Annex IV (light) |
| minimal | Art. 50 only (where applicable) |
| gpai | Arts. 51–55; Annex XI; Annex XII |

```python
def regulatory_coverage_pct(state: AuditState) -> float:
    in_scope = ARTICLE_SET[state["risk_tier"]]       # constant table above
    covered = {a for a in in_scope
               if any(art_cite.startswith(a)
                      for art in state["compliance_matrix"][a].evidence_citations)}
    return 100.0 * len(covered) / max(len(in_scope), 1)
```

**Benchmark.** All three KPIs are computed for AAA *and* for the supervisor's human audit on the same case-study artefacts; the delta is reported in T18 and in the workshop paper.

**Acceptance thresholds** (set by exposé Sub-Q 3 success criterion):

| KPI | When evaluated | PASS | PASS_WITH_OBSERVATIONS | FAIL / Block |
|---|---|---|---|---|
| `intake_completeness_score` | End of Stage B (before Phase 1) | ≥ 0.90 | 0.80 – 0.89 | < 0.80 → **Phase 1 blocked** |
| `completeness_score` | Stage 6 (Compliance Matrix) | ≥ 0.90 | 0.75 – 0.89 | < 0.75 |
| `regulatory_coverage_pct` | Stage 6 (Compliance Matrix) | ≥ 90 | 75 – 89 | < 75 |

A `PASS` final verdict requires all three KPIs in their PASS or PASS_WITH_OBSERVATIONS bands **and** all conditions of §6 Stage 6 satisfied.

### 9.2 Tracing

- **Langfuse + OpenTelemetry** spans on every agent invocation, tool call, and state transition (both Apache-2.0, self-hostable).
- Trace ID embedded in every Evidence Store artefact for full lineage.
- Cost dashboard: tokens per phase, per agent, per engagement — surfaces drift toward Anthropic's 15× ceiling.

### 9.3 Guardrails

**Intake-level guardrails** (before any LLM receives client data):
- **Schema validation first**: `annex_iv_validator` runs JSON-Schema validation against the Annex IV §1–§9 bundle *before* any field is passed to an LLM context. Invalid payloads are rejected at the API layer with a field-level error list; they never enter the agent graph.
- **Intake completeness gate**: `intake_completeness_calculator` must return `intake_completeness_score ≥ 0.80` before the Orchestrator instantiates any phase agent. This is enforced as a precondition in `aaa/graph.py`; it is not a soft warning.
- **Credential isolation**: Stage C scoped credentials are stored as OpenBao secrets; only the secret path is written to `AuditState`. The actual token is fetched in-process by the Phase 1 agent at runtime and is never logged or serialised.

**Phase-level input guardrails**:
- **PII redaction**: all Stage B free-text fields and uploaded documents are passed through the PII redactor before reaching any LLM context window. The redactor replaces named individuals, email addresses, and IBAN/SSN patterns with `[REDACTED_PII]` tokens.
- **Injection hardening**: Stage A and Stage B free-text fields are quoted as *data* (not *instructions*) in every agent prompt template; the `triage_render` tool enforces this by inserting a `###DATA###` delimiter and refusing to render prompts that would allow instruction injection.

**Output guardrails**:
- Every report artefact passes a final policy check: no leaked PII, no unverified claims, every regulatory citation backed by a RAG-source URL.
- The `declaration_diff` output is appended verbatim to T02 and T01c as structured JSON — not rendered through an LLM — to prevent hallucination of declared vs verified values.

---


## 10. Deployment & Runtime Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Orchestration framework | **LangGraph** (MIT) | Explicit state graph + Postgres checkpointer; matches the deterministic phase ordering the EU AI Act requires. |
| Agent runtime | LangChain (MIT) agents on top of LangGraph nodes | Mature tool-calling, structured-output support |
| Model routing | **LiteLLM** (MIT) | Single OSS wrapper calling Anthropic Claude, OpenAI GPT, DeepSeek, Mistral, local Ollama, etc. — no provider lock-in |
| Vector store | **Qdrant** (Apache-2.0, local Docker) | Regulatory corpus + RAG over past engagements; replaces pgvector — no Postgres extension required |
| Object store | **MinIO** (AGPL-v3, S3-wire-compatible) | Evidence Store; identical API in dev and prod |
| Relational store | **PostgreSQL** | `AuditState` checkpoints, `evidence` index, engagement metadata |
| Queue | **Valkey Streams** (BSD-3, Linux-Foundation Redis fork) | Inter-stage dispatch on parallel branches |
| Front-end | **Next.js** (MIT) client portal, self-hosted in a Node container | Self-serve intake, status, report download |
| API | **FastAPI** (MIT) | Engagement CRUD; outbound HTTP client calling the **S4 FastAPI** `cgsa_pull` endpoint (§10.2) |
| Observability | **Langfuse** (Apache-2.0, self-hosted) + **Grafana** + **Loki** + **OpenTelemetry** | Traces, dashboards, log aggregation |
| Secrets | **OpenBao** (MPL-2.0, Linux-Foundation Vault fork) | Per-engagement scoped credentials to client model APIs |

### 10.1 Process Topology

- **One Orchestrator process per engagement** (long-lived, stateful, pinned to a checkpoint thread).
- **Worker pool** for phase agents — horizontally scalable, stateless between dispatches.
- **Tool-server processes** — each deterministic tool family runs as an independent MCP server so a crash in `shap_explain` cannot take down the Orchestrator.

### 10.2 S4 → S5 Interface Contract (S4 FastAPI endpoint)

Per the exposé (line 150: *"S5 AAA calls S4 CGSA as an API endpoint for the governance phase"*) the integration direction is **AAA pulls from S4's FastAPI server** — never push. S4 runs its own FastAPI application (separate process/container, `S4_CGSA_BASE_URL` in `.env`) that exposes the CGSA assessment results. The Orchestrator decides *when* governance evidence is needed (entry to Phase 5) and requests it then, keeping the S5 audit lifecycle authoritative.

**S4 FastAPI endpoint** (implemented and maintained by the S4 team):

```
GET  {S4_CGSA_BASE_URL}/api/v1/assessments/{assessment_id}
Accept: application/json
Header: X-Schema-Version: 1.0.0
Header: Authorization: Bearer <token from OpenBao>
```

The response body is the `uagf_cgsa_aaa_schema.json` payload (schema version `1.0.0`). S4 sets `X-Schema-Version` in the response header; AAA asserts the match before parsing.

**Tool: `cgsa_pull`** (§4.5) — invoked at the start of Phase 5:

**Handler flow** (executed inside the Phase 5 node):

1. **Resolve `assessment_id`** — taken from `client_submission.cgsa_assessment_id` (set at intake; provided by the client or by the supervisor during S4↔S5 integration test).
2. **Pull** — HTTP GET to S4's FastAPI with exponential back-off (5 attempts, 1–32 s). 404 ⇒ HITL escalation ("CGSA assessment not yet available"). 5xx ⇒ retry. 401 ⇒ refresh OpenBao token once, then HITL.
3. **Pin-check** — assert `response.headers["X-Schema-Version"] == "1.0.0"`; on drift ⇒ Verifier `escalate_hitl` with full diff.
4. **`schema_validate`** against the pinned `uagf_cgsa_aaa_schema.json` (vendored in `aaa/schemas/cgsa/v1.0.0/`).
5. **Persist** the raw payload to MinIO under `engagements/{engagement_id}/cgsa/{assessment_id}.json` with SHA-256 in the `evidence` table.
6. **Hydrate** `AuditState` per the §5.4 consumption map (every CGSA-prefixed field set in one transaction).
7. **Cross-check** Phase 1 `risk_tier` vs `metadata.risk_tier`; mismatch ⇒ `cgsa_risk_tier_match = False` and HITL flag (§8.4).
8. **Emit** `cgsa_ingested` span (Langfuse) with `assessment_id`, byte size, validation duration.

**Schema-drift CI gate.** A nightly GitHub Actions job (`s4_contract.yml`) pulls the live `uagf_cgsa_aaa_schema.json` from the S4 repo and runs `jsonschema_diff` against the vendored copy. Any breaking change opens an issue and fails the build until either AAA updates its pinned version or S4 reverts.

**Offline / demo mode.** For the Streamlit demo (§14) and unit tests, `cgsa_pull` is monkey-patched to read `tests/fixtures/cgsa/{scenario}.json`. The fixtures include: `compliant_high.json`, `partially_compliant_high.json`, `non_compliant_high.json`, `limited_tier.json`, `gpai.json`, `low_confidence_extraction.json`, `schema_v090_drift.json` (negative case).

---

## 11. Security & Multi-Tenancy

| Concern | Control |
|---------|---------|
| Client data isolation | Per-engagement Postgres schema + per-engagement MinIO bucket prefix + per-engagement IAM policy |
| Model API credentials | Scoped tokens in OpenBao; never inlined in agent prompts |
| **Stage C scoped credentials** | Client provides credentials via the portal's secure vault form; stored in OpenBao under `engagements/{id}/stage_c/`; only the secret path is written to `AuditState.client_submission.stage_c.credential_ref`. Access scope and expiry enforced by the vault policy; credentials auto-revoked on engagement close (webhook called at `stage_c.revocation_webhook`). |
| **Declaration tampering prevention** | T01a is written once at Stage A submission and is content-addressed (SHA-256 stored in `evidence` table). Any attempt to modify Stage A after submission is rejected by the `evidence` index (append-only rows); the Verifier re-checks the SHA-256 before running `declaration_diff`. |
| Prompt injection from client-supplied documents | Input guardrail strips instructions; Stage A/B free-text quoted as data with `###DATA###` delimiter (§9.3); documents are quoted as data, never executed as instructions |
| Audit-log immutability | `evidence` index rows are append-only; SHA-256 chain across artefacts per engagement |
| GDPR | DPA per client; right-to-erasure honoured by purging engagement schema + MinIO prefix + OpenBao secrets; Regulatory RAG and golden-eval sets never store client data |
| **Intake data minimisation** | Stage B upload is the minimum set required by Annex IV; any additional client data provided voluntarily is not stored beyond the engagement window. Conditional L-branch fields (system prompt, guardrail config) are encrypted at rest in MinIO using per-engagement KMS keys managed by OpenBao. |

---

## 12. Mapping to the Source Articles

Engineering tactics from the MAS blog set are listed first; academic methodology citations follow. Both sets are load-bearing — the academic set governs *what* the system must do, the MAS set governs *how* it runs.

| Source insight | Where it lives in this architecture |
|----------------|--------------------------------------|
| **Engineering (MAS) sources** | |
| n8n — *Supervisor / hierarchical pattern* | Orchestrator + Verifier (§3.1) over Phase agents (§3.2) |
| n8n — *Sequential pipeline* | Phases 1 → (2,3,4 ‖) → 5 → 6 in §6 |
| n8n — *Tools ≠ agents* | §4 tool catalogue |
| dev.to — *3–7 agents per workflow* | Standard branch invokes ≤7 active agents (§7) |
| dev.to — *Governance & observability from day 1* | §9 (eval, tracing, guardrails) |
| LangChain — *Subagents (context isolation)* | Phase agents receive only the dispatch brief + URIs, not full state (§5.3) |
| LangChain — *Router pattern* | Phase 1 → standard vs L-branch (§6) |
| LangChain — *Skills / progressive disclosure* | Tier-3 Cyber + Privacy agents loaded on demand (§3.3) |
| Anthropic — *Lead agent + parallel subagents* | Orchestrator dispatches Phases 2/3/4 in parallel (§6) |
| Anthropic — *Filesystem hand-off* | Evidence Store with URI passing (§5.2) |
| Anthropic — *Eval with LLM-as-judge + human review* | §9.1 four-tier evaluation |
| Anthropic — *Checkpointing & resume* | LangGraph PostgresSaver (§8.3) |
| Anthropic — *Token cost ≈ 15×* | Accepted; tracked on cost dashboard (§9.2) |
| **Academic (methodology) sources** | |
| Mökander 2023 — *Three-layered audit (governance / model / application)* | 6-phase protocol decomposition; Tier-3 application-layer audits (§3.3, §1.1) |
| Koshiyama 2022 — *Practitioner-gap analysis; need for standardised completeness measures* | `completeness_score` and `regulatory_coverage_pct` KPIs (§9.1); open-source template registry (§4A) |
| Wang 2024 — *Autonomous-agent role specialisation* | 12-agent role taxonomy (§3); Orchestrator planner-executor pattern (§6) |
| Falco 2021 — *Independent audit principle* | Verifier as independent agent (§3.1); Tier-3 Cyber sub-agent independence (§3.3) |
| Gebru 2021 — *Datasheets for Datasets* | T06 datasheet template (§4A); Phase 2 evidence rubric; Stage B `training_data_description` field (Annex IV §2) |
| **Mitchell 2019 — *Model Cards for Model Reporting*** | T02 system card template (§4A); Stage A triage form structure (provider, intended purpose, deployment context, performance metrics) — Model Cards are the practitioner predecessor of the Annex IV §1 general description requirement. |
| **Arnold 2019 — *FactSheets: Increasing Trust in AI Services through Supplier's Declarations of Conformity*** | Stage A self-declaration pattern; `declared_*` fields in `StageATriage`; the concept of client-declared values verified by an independent auditor maps directly to IBM's FactSheet supplier-declaration model. |
| EU AI Act 2024 — *Art. 9, 11, 43, Annex III, Annex IV* (primary specification) | §3.5 (Art. 43 procedure selection), §3.6 (Annex III taxonomy), §6 Stage 0 (three-stage intake aligned with Art. 11 + Annex IV §1–§9), §6.2 (risk-tier CSP), §5.4 (Art. 9/10/13/14/17 hand-off from S4) |

---

## 13. Summary

The AAA is a **hub-and-spoke orchestrator-worker system of 12 agents** that consumes the S4 `uagf_cgsa_aaa_schema.json` payload via a pull at Phase 5 (§10.2) and emits an EU AI Act-compliant conformity-assessment report at Phase 6 covering **Articles 9, 10, 11, 13, 14, 15, 17, 43, Annex III, Annex IV, and GPAI 51–55**. Engagements begin with a three-stage Annex-IV-aligned intake — Stage A triage (modality / risk / Annex III declaration), Stage B dossier (Annex IV §1–§9 technical documentation), Stage C scoped live-system access — captured as templates T01a/T01b/T01c and validated against published JSON Schemas before Phase 1 runs (§6 Stage 0). Three always-on cross-cutting agents (Orchestrator, Verifier, Regulatory RAG) coordinate six phase agents through a LangGraph state machine, with a Router fork at Phase 1 sending LLM/agentic systems down the UAGF-TAM-L branch and progressive-disclosure spawns of Cyber and Privacy specialists when their evidence is needed (Tier-3 agents justified by Mökander 2023 application-layer audit obligations, §3.3). Twenty MIT-licensed artefact templates (§4A) are the durable currency between agents; the Orchestrator's deterministic Article 43 procedure selector (§3.5) and the published Risk-Tier × Phase CSP catalogue (§6.2) make every routing decision regulator-replayable. Three operational KPIs — `intake_completeness_score`, `completeness_score`, and `regulatory_coverage_pct` (§9.1) — are computed deterministically on every engagement and benchmarked against the supervisor's human audit on the four thesis case studies. The Ready-to-Deploy Plan (§14) makes every exposé milestone executable via a single `make` target, from `make m3-linear` (Week 7) through `make deploy-prod` (Week 24).

---

## 14. Ready-to-Deploy Plan

This section is the operational counterpart to §1–§13: every component declared above has a build, a runtime command, and a smoke test. The plan is staged so the exposé Week-by-Week milestones (M1–M9) are each satisfiable by running a single `make` target.

### 14.1 Repository Layout

```
UAGF_TAM/
├── ARCHITECTURE.md                      # this document
├── pyproject.toml                       # package metadata (build backend only; deps in requirements files)
├── requirements.txt                     # runtime dependencies (pip-managed)
├── requirements-dev.txt                 # dev/test dependencies (-r requirements.txt + lint/test tools)
├── Makefile                             # one-line targets per milestone
├── docker-compose.yml                   # local dev: Postgres, Qdrant, MinIO, Valkey, Langfuse, OpenBao
├── docker-compose.prod.yml              # production overlay
├── .github/
│   └── workflows/
│       ├── ci.yml                       # lint + pytest + coverage gate
│       ├── s4_contract.yml              # nightly schema-drift check (§10.2)
│       ├── templates_release.yml        # publishes uagf-tam-templates to PyPI
│       └── streamlit_deploy.yml         # demo deployment to Streamlit Cloud
├── aaa/
│   ├── __init__.py
│   ├── settings.py                      # pydantic-settings; reads env vars
│   ├── agents/
│   │   ├── tier1/{orchestrator,verifier,regulatory_rag}.py
│   │   ├── tier2/{p1_scope,p2_data,p3_model,p4_output,p5_governance,p6_report}.py
│   │   └── tier3/{l_branch,cyber,privacy}.py
│   ├── tools/                           # §4 deterministic tools (one file per family)
│   │   ├── data/, model/, fairness/, llm/, governance/
│   ├── state.py                         # AuditState TypedDict (§5.1)
│   ├── graph.py                         # LangGraph definition (§6)
│   ├── csp.py                           # Risk-Tier × Phase CSP (§6.2)
│   ├── art43.py                         # select_art43_procedure (§3.5)
│   ├── annex_iii.py                     # AnnexIIIEntry + classifier (§3.6)
│   ├── cgsa/                            # §10.2 pull client + parsers
│   │   ├── pull.py
│   │   ├── ingest.py
│   │   └── fixtures/                    # offline-mode JSON
│   ├── intake/                          # §6 Stage 0 — three-stage intake pipeline
│   │   ├── triage.py                    # StageATriage form handler + art43_preview call
│   │   ├── dossier.py                   # AnnexIVDossier upload handler + annex_iv_validator
│   │   ├── completeness.py              # intake_completeness_calculator (§9.1 KPI 0)
│   │   ├── diff.py                      # declaration_diff tool (declaration_verification map)
│   │   └── fixtures/                   # offline Stage A/B fixtures for demo + tests
│   ├── evidence/
│   │   ├── store.py                     # MinIO + Postgres index
│   │   └── schemas/                     # T01a–T18 JSON Schemas
│   ├── eval/
│   │   ├── intake_completeness.py       # §9.1 KPI 0 (intake_completeness_score)
│   │   ├── completeness.py              # §9.1 KPI 1
│   │   ├── coverage.py                  # §9.1 KPI 2
│   │   └── llm_judge.py
│   ├── api/                             # FastAPI app (engagement CRUD)
│   │   └── main.py
│   └── ui/                              # Streamlit demo (§14.7)
│       └── app.py
├── schemas/
│   └── cgsa/v1.0.0/uagf_cgsa_aaa_schema.json    # vendored S4 schema (pinned)
├── templates/                           # 20 Jinja2 partials (T01a/T01b/T01c + T02–T18)
│   └── intake/                          # T01a, T01b, T01c partials + JSON schemas
├── tests/
│   ├── unit/                            # per-agent + per-tool
│   ├── contract/                        # CGSA pull + schema drift
│   ├── golden/                          # frozen end-to-end traces
│   └── e2e/                             # German Credit, M5, Hamburg, LLM cases
├── infra/
│   ├── tofu/                            # OpenTofu modules (Hetzner / Scaleway)
│   └── runbook.md                       # ops playbook (§14.6)
└── data/                                # exposé, schemas, sample inputs (gitignored client data)
```

### 14.2 Dependency Manifest (`requirements.txt` / `requirements-dev.txt`)

Dependencies are managed with plain `pip` inside a Python `venv`. Two files are committed: `requirements.txt` (runtime) and `requirements-dev.txt` (extends runtime with test/lint tooling). Minimum versions are specified in these files to ensure compatibility while allowing minor updates; there is no separate lock format.

**`requirements.txt` (excerpt — pinned major versions shown):**

```
# orchestration
langgraph>=0.2
langchain>=0.3
litellm>=1.50
# tooling
python-constraint>=1.4
jsonschema>=4.23
pydantic>=2.9
pydantic-settings>=2.5
pandas>=2.2
scikit-learn>=1.5
scipy>=1.14
ydata-profiling>=4.10
evidently>=0.4
presidio-analyzer>=2.2
shap>=0.46
lime>=0.2
grad-cam>=1.5
torchmetrics>=1.4
fairlearn>=0.11
aif360>=0.6
ragas>=0.2
trulens-eval>=1.2
garak>=0.9.0
promptfoo>=0.1
detoxify>=0.5
llama-index>=0.11
qdrant-client>=1.9
# storage + infra clients
psycopg[binary]>=3.2
sqlalchemy>=2.0
minio>=7.2
redis>=5.0
# api + ui
fastapi>=0.115
uvicorn[standard]>=0.32
streamlit>=1.39
httpx>=0.27
# reporting
reportlab>=4.2
jinja2>=3.1
# observability
langfuse>=2.50
opentelemetry-sdk>=1.27
```

**`requirements-dev.txt`:**

```
-r requirements.txt
pytest>=8.3
pytest-asyncio>=0.24
pytest-cov>=5.0
ruff>=0.7
mypy>=1.13
pre-commit>=4.0
```

Install:

```bash
python -m venv .venv
source .venv/bin/activate               # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .                        # editable install of the aaa package
pre-commit install
```

### 14.3 Configuration & Secrets (`.env.example`)

All runtime configuration is environment-driven (12-factor). No secret is ever committed.

```bash
# --- core ---
AAA_ENV=dev                              # dev | staging | prod
AAA_LOG_LEVEL=INFO

# --- model routing (LiteLLM) ---
ANTHROPIC_API_KEY=                       # required for Opus / Sonnet / Haiku
OPENAI_API_KEY=                          # fallback
DEEPSEEK_API_KEY=                        # cost-saver fallback
LITELLM_FALLBACKS="claude-opus-4>claude-sonnet-4>gpt-4o-mini"

# --- storage ---
POSTGRES_DSN=postgresql://aaa:aaa@localhost:5432/aaa
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=aaa
MINIO_SECRET_KEY=aaa-secret              # rotate via OpenBao in prod
VALKEY_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333         # Qdrant REST API (local Docker)

# --- S4 CGSA integration (§10.2) ---
S4_CGSA_BASE_URL=http://localhost:8001   # S4 FastAPI server (adjust to deployed URL in staging/prod)
S4_CGSA_TOKEN_PATH=secret/aaa/s4         # OpenBao path
CGSA_SCHEMA_VERSION=1.0.0

# --- observability ---
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

# --- demo mode ---
AAA_OFFLINE_MODE=false                   # true ⇒ cgsa_pull reads fixtures
```

### 14.4 Local Bootstrap (`docker-compose.yml`)

A single `docker compose up -d` brings every dependency of §10 online. Versions are pinned and match the §10 table.

```yaml
services:
  postgres:
    image: postgres:16
    environment: { POSTGRES_DB: aaa, POSTGRES_USER: aaa, POSTGRES_PASSWORD: aaa }
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck: { test: ["CMD","pg_isready","-U","aaa"], interval: 5s, retries: 10 }

  qdrant:
    image: qdrant/qdrant:v1.9.4            # local Docker — no cloud account required
    ports: ["6333:6333","6334:6334"]       # 6333 = REST, 6334 = gRPC
    volumes: ["qdrantdata:/qdrant/storage"]
    healthcheck: { test: ["CMD","curl","-f","http://localhost:6333/readyz"], interval: 5s, retries: 10 }

  minio:
    image: minio/minio:RELEASE.2025-01-20T14-49-07Z
    command: server /data --console-address ":9001"
    environment: { MINIO_ROOT_USER: aaa, MINIO_ROOT_PASSWORD: aaa-secret }
    ports: ["9000:9000","9001:9001"]
    volumes: ["miniodata:/data"]
    healthcheck: { test: ["CMD","curl","-f","http://localhost:9000/minio/health/live"], interval: 5s }

  valkey:
    image: valkey/valkey:8
    ports: ["6379:6379"]

  langfuse:
    image: langfuse/langfuse:2
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://aaa:aaa@postgres:5432/aaa
      NEXTAUTH_SECRET: dev-only-do-not-reuse
      NEXTAUTH_URL: http://localhost:3000
    ports: ["3000:3000"]

  openbao:
    image: openbao/openbao:2
    cap_add: [IPC_LOCK]
    environment:
      BAO_DEV_ROOT_TOKEN_ID: dev-root
      BAO_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    ports: ["8200:8200"]

volumes: { pgdata: {}, qdrantdata: {}, miniodata: {} }
```

Bootstrap sequence:

```bash
cp .env.example .env && $EDITOR .env                # add API keys
docker compose up -d                                # bring up Postgres, Qdrant, MinIO, Valkey, Langfuse, OpenBao
source .venv/bin/activate                           # activate Python venv (created in §14.2)
python -m alembic upgrade head                      # apply schema migrations (engagements, evidence, checkpoints)
python -m aaa.cli init-storage                      # create MinIO buckets + seed Qdrant with EU AI Act corpus
python -m aaa.cli seed-fixtures                     # load CGSA fixtures (offline mode)
python -m pytest tests/unit                         # gate: must pass before first audit
```

### 14.5 Makefile — One Target per Milestone

The exposé milestones (M1–M9) map one-to-one onto `make` targets. Each target produces a verifiable artefact.

```makefile
PYTHON := .venv/bin/python
PIP    := .venv/bin/pip

.PHONY: venv install up down lint test coverage \
        intake-validate intake-demo \
        m3-linear m4-full m5-case1 m5-case2 m6-case3 m6-case4 \
        report-german demo deploy-staging deploy-prod

venv:
	python -m venv .venv

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	.venv/bin/pre-commit install

up:       ; docker compose up -d && $(PYTHON) -m alembic upgrade head
down:     ; docker compose down
lint:     ; .venv/bin/ruff check . && .venv/bin/mypy aaa/
test:     ; $(PYTHON) -m pytest -q
coverage: ; $(PYTHON) -m pytest --cov=aaa --cov-report=term-missing --cov-fail-under=80

# --- intake targets ---
intake-validate:; $(PYTHON) -m aaa.cli intake validate --fixture aaa/intake/fixtures/german_credit_stage_b.json
                # Runs annex_iv_validator + intake_completeness_calculator; prints score + field list
intake-demo:    ; AAA_OFFLINE_MODE=true $(PYTHON) -m aaa.cli intake demo --case german_credit
                # Simulates the full Stage A → B → C wizard in the terminal using offline fixtures

# --- exposé milestones ---
m3-linear:    ; $(PYTHON) -m aaa.cli run --case german_credit --pipeline linear   # M3 (Week 7)
m4-full:      ; $(PYTHON) -m aaa.cli run --case german_credit --pipeline full     # M4 (Week 11)
m5-case1:     ; $(PYTHON) -m aaa.cli run --case german_credit --emit-pdf          # M5 Finance
m5-case2:     ; $(PYTHON) -m aaa.cli run --case m5_forecasting --emit-pdf         # M5 Retail
m6-case3:     ; $(PYTHON) -m aaa.cli run --case hamburg_hub --emit-pdf            # M6 live
m6-case4:     ; $(PYTHON) -m aaa.cli run --case llm_open --emit-pdf --branch l    # M6 UAGF-TAM-L

# --- demo + deploy ---
report-german:; $(PYTHON) -m aaa.cli run --case german_credit --emit-pdf --open
demo:         ; AAA_OFFLINE_MODE=true .venv/bin/streamlit run aaa/ui/app.py
deploy-staging:; tofu -chdir=infra/tofu workspace select staging && tofu -chdir=infra/tofu apply -auto-approve
deploy-prod:  ; tofu -chdir=infra/tofu workspace select prod    && tofu -chdir=infra/tofu apply
```

### 14.6 CI/CD (GitHub Actions)

Four workflows, each in `.github/workflows/`.

| Workflow | Trigger | Purpose | Failure policy |
|---|---|---|---|
| `ci.yml` | push, PR | ruff, mypy, pytest, coverage ≥ 80%, build artefact-template package | Block merge |
| `s4_contract.yml` | cron `0 2 * * *` + manual | Pull S4 schema, run `jsonschema_diff` vs `schemas/cgsa/v1.0.0/`, open issue on drift | Open issue, do not auto-merge schema bump |
| `templates_release.yml` | tag `tpl-v*` | Build + publish `uagf-tam-templates` to PyPI under MIT licence | Skip if version exists |
| `streamlit_deploy.yml` | push to `main` (paths: `aaa/ui/**`) | Redeploy demo to Streamlit Cloud with `AAA_OFFLINE_MODE=true` | Notify Slack on failure |

`ci.yml` reference job:

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:16, env: { POSTGRES_PASSWORD: aaa, POSTGRES_USER: aaa, POSTGRES_DB: aaa }, ports: ['5432:5432'], options: '--health-cmd pg_isready --health-interval 5s' }
      qdrant:   { image: qdrant/qdrant:v1.9.4, ports: ['6333:6333'] }
      minio:    { image: minio/minio:RELEASE.2025-01-20T14-49-07Z, ports: ['9000:9000'], env: { MINIO_ROOT_USER: aaa, MINIO_ROOT_PASSWORD: aaa-secret } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: python -m venv .venv
      - run: .venv/bin/pip install --upgrade pip
      - run: .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pip install -e .
      - run: .venv/bin/ruff check .
      - run: .venv/bin/mypy aaa/
      - run: .venv/bin/pytest --cov=aaa --cov-fail-under=80
      - run: .venv/bin/python -m aaa.cli run --case german_credit --pipeline full --offline   # golden smoke
```

### 14.7 Streamlit Demo (`aaa/ui/app.py`)

The thesis Deliverable 1 (line 82) is *"Deployed on Streamlit Cloud (demo version with sample AI system)"*. The demo runs the full LangGraph pipeline in `AAA_OFFLINE_MODE=true`, with CGSA payload sourced from `aaa/cgsa/fixtures/`.

Pages:

1. **Stage A — Triage** — The demo pre-fills all ~20 Stage A fields from `aaa/intake/fixtures/german_credit_stage_a.json` when the user clicks "Load German Credit example". The `art43_preview` result is displayed immediately so the user sees the expected conformity-assessment procedure before uploading any artefact. In the production Next.js portal, this is a two-step wizard (form → preview confirmation).
2. **Stage B — Annex IV Dossier** — Upload Annex IV §1–§9 documentation. In the demo, all fields are pre-filled from `german_credit_stage_b.json`. The `annex_iv_validator` runs on submission and the `intake_completeness_score` is displayed with a per-section breakdown. Fields below the 0.80 gate are highlighted in red with a remediation hint. *(Note: the "Load German Credit example" button is a shortcut that bypasses the completeness gate for demo purposes — `intake_completeness_score` is forced to 1.0 in offline mode.)*
3. **Stage C — Scoped Access** (skipped in offline demo) — In offline mode this step shows a read-only summary of what would be collected (endpoint URL, access scope, expiry). In the production portal a secure vault form is rendered by the Next.js frontend; no credentials flow through Streamlit.
4. **Live audit** — Streams Langfuse trace events from the running engagement, one row per phase. Each row shows: phase id, agent, status (`pending`/`running`/`accept`/`rerun`/`escalated`), token/time spent, link to artefact in MinIO.
5. **Report** — When `final_verdict` is set, renders T18 PDF inline (PDF.js component) with a download button. Side panel shows all three KPIs (`intake_completeness_score`, `completeness_score`, `regulatory_coverage_pct`) against the case-study human-expert benchmark.
6. **Trace explorer** — Embedded Langfuse UI for replay/time-travel debugging.

Streamlit Cloud deployment: connect the GitHub repo; set `AAA_OFFLINE_MODE=true`, `ANTHROPIC_API_KEY` (sandbox key) as secrets; `streamlit_deploy.yml` redeploys on every push to `main`.

### 14.8 Production Topology (`infra/tofu/`)

The same containers from §14.4 ship to production via OpenTofu modules. Single VPC, two AZs, no provider lock-in (Hetzner Cloud or Scaleway). The production overlay adds: TLS termination at Caddy, automated backups of MinIO + Postgres to off-site S3 via `restic`, OpenBao seal/unseal procedure documented in the runbook.

```mermaid
flowchart LR
  classDef edge fill:#cfd8dc,stroke:#546e7a,color:#0b1f08
  classDef app  fill:#5b6cff,stroke:#2a3aad,color:#ffffff
  classDef data fill:#7fb069,stroke:#3f6a32,color:#0b1f08
  classDef obs  fill:#f4c95d,stroke:#8a6a14,color:#2a1f06

  USR[/"Client / Auditor"/]:::edge
  CADDY["Caddy<br/>TLS + rate-limit"]:::edge
  UI["Streamlit / Next.js"]:::app
  API["FastAPI<br/>(AAA)"]:::app
  ORCH["Orchestrator workers<br/>(one per engagement)"]:::app
  WRK["Phase + Tier-3 worker pool"]:::app
  TOOLS["MCP tool servers<br/>(SHAP, fairlearn, RAGAs, …)"]:::app
  PG[("Postgres 16<br/>checkpoints + evidence index")]:::data
  QD[("Qdrant<br/>Vector Store")]:::data
  MIN[("MinIO<br/>Evidence Store")]:::data
  VAL[("Valkey<br/>Streams")]:::data
  BAO[("OpenBao<br/>Secrets")]:::data
  LF["Langfuse + Grafana + Loki"]:::obs
  S4["S4 FastAPI<br/>(CGSA endpoint)"]:::edge

  USR --> CADDY --> UI --> API --> ORCH
  ORCH --> WRK --> TOOLS
  ORCH --> PG
  ORCH --> QD
  ORCH --> MIN
  ORCH --> VAL
  ORCH --> BAO
  ORCH -->|"GET /api/v1/assessments/{id}"| S4
  WRK --> LF
  TOOLS --> LF
```

### 14.9 Operational Runbook (`infra/runbook.md` — summary)

| Incident | Detection | First action | Escalation |
|---|---|---|---|
| Engagement stuck > 2 h | Cost dashboard SLA breach | `aaa.cli resume --engagement {id}` (uses LangGraph checkpoint) | HITL if 3 reruns fail |
| `cgsa_pull` 5xx > 5 min | Langfuse alert | Check S4 status page; flip engagement to HITL pause | Email supervisor |
| Schema drift on nightly contract | GitHub issue auto-opened | Inspect diff; if non-breaking, bump pinned version + PR; if breaking, freeze new audits | Joint S4↔S5 sync meeting |
| MinIO disk > 80% | Grafana | Run `restic forget --keep-last 30` on backups; scale volume | On-call rota |
| LLM provider outage | LiteLLM fallback engaged automatically | Verify fallback model in cost dashboard; downgrade audit confidence flag | If all fallbacks down, pause new engagements |
| Verifier `escalate_hitl` spike | Langfuse anomaly | Inspect last 10 critiques; if prompt regression, roll back agent prompt version | Notify prompt-owner |
| Client right-to-erasure request | GDPR ticket | `aaa.cli purge --engagement {id}` (drops Postgres schema + MinIO prefix) | Log in DPA register |

### 14.10 Smoke-Test Procedure (10-Minute Acceptance)

Run after every deploy and after every milestone target. All eleven steps must pass.

1. `make up` — every container healthy in `docker compose ps` (including Qdrant at `:6333`).
2. `curl -fsS http://localhost:8000/healthz` returns `{"status":"ok","schema_version":"1.0.0"}`.
3. `.venv/bin/python -m aaa.cli check-cgsa-schema` — pinned schema matches vendored; curl S4 FastAPI healthz at `$S4_CGSA_BASE_URL/healthz`.
4. **`make intake-validate`** — `annex_iv_validator` and `intake_completeness_calculator` run against `german_credit_stage_b.json`; `intake_completeness_score >= 0.95` (full fixture); output prints per-section scores with no missing required fields.
5. **`make intake-demo`** — simulates Stage A → B → C wizard in offline mode; `art43_preview` printed; T01a/T01b/T01c written to MinIO; no exceptions.
6. `make m3-linear` — produces 6 admitted artefacts (T01a, T01b, T01c, T02, T04, T06) in MinIO; `completeness_score >= 0.30`.
7. `make m4-full` — produces 19 of 20 templates (T16 skipped on non-LLM); PDF rendered in ≤ 2 hours wall-clock (exposé SLA); `intake_completeness_score >= 0.80`, `completeness_score >= 0.85`, `regulatory_coverage_pct >= 80`.
8. `.venv/bin/pytest tests/intake/test_completeness.py` — unit tests for `intake_completeness_calculator` covering all nine Annex IV sections + L-branch conditional fields; all cases pass.
9. `.venv/bin/pytest tests/contract/test_cgsa_pull.py` — pull from S4 FastAPI, validate, hydrate against all fixtures in `aaa/cgsa/fixtures/`.
10. `.venv/bin/pytest tests/e2e/test_uagf_tam_l.py` — L-branch end-to-end produces T16; UAGF-TAM-L PDF emitted; `intake_completeness_score` present in T01c.
11. Open Streamlit demo at `http://localhost:8501`, click "Load German Credit example", verify Stage A triage page shows `art43_preview`; proceed through Stage B; observe `intake_completeness_score` displayed; click through to live trace; download PDF; verify it contains T05 (Article 43 decision), T17 (compliance matrix), and T01c (intake completeness report).

### 14.11 Exposé Milestone ↔ Deployment Checklist

| Milestone | Week | Definition-of-done (deployable artefact) |
|---|---|---|
| M1 Kickoff | 1 | `make install up` succeeds on student laptop; Hamburg Hub DPA signed; CGSA schema vendored in `schemas/cgsa/v1.0.0/`. |
| M2 Protocol Finalised | 4 | 20 templates committed in `templates/` (T01a/T01b/T01c + T02–T18) with JSON Schemas; `make intake-validate` passes on German Credit fixture; §6.2 CSP catalogue published; joint S4↔S5 meeting minutes attached; supervisor sign-off on `csp.py`. |
| M3 Linear Pipeline | 7 | `make m3-linear` produces a rough PDF on German Credit; CI green. |
| M4 Full AAA Pipeline | 11 | `make m4-full` emits compliant PDF with all six phases + T05 (Art. 43) + T17 (compliance matrix) in ≤ 2 h. |
| M5 Case Studies 1+2 | 15 | `make m5-case1 m5-case2`; benchmarks vs supervisor's human audit recorded in T18; all three KPIs (`intake_completeness_score`, `completeness_score`, `regulatory_coverage_pct`) in PASS or PASS_W_OBS band. |
| M6 Case Studies 3+4 | 17 | `make m6-case3 m6-case4`; Hamburg Hub sign-off captured; UAGF-TAM-L PDF emitted; 4-case comparison table generated by `aaa.cli compare`. |
| M7 Paper Draft | 19 | Workshop paper draft references trace IDs from M5/M6 runs (full reproducibility). |
| M8 Submit | 21 | Streamlit Cloud demo URL live; GitHub repo public with MIT licence on `uagf-tam-templates`; PyPI package published. |
| M9 Final | 24 | `tofu apply` against `prod` workspace; thesis appendix lists every container image digest used in the final audits. |
