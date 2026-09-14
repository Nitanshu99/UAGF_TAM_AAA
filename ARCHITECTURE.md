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

> **Implementation status (current repo snapshot)**
>
> The repository now implements the thesis MVP end-to-end: prompt runtime sourced
> from `PROMPT.md`, client-document ingestion/search via per-engagement Qdrant
> collections, materiality-aware findings and remediation fields, management-
> response shells, risk heat-map + maturity radar generation, formal auditor
> opinion generation, and a minimal customer upload → run → report workflow
> across CLI, FastAPI, and Streamlit.

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

## 3. Agent Roster (14 Agents)

The roster is partitioned into three tiers. Tier-1 agents are always active; Tier-2 agents run once per engagement; Tier-3 agents are spawned on demand.

Model assignments follow a cost-vs-capability rule, implemented in `aaa/platform/model_registry/` as the single source of truth, on OpenAI's GPT-5.6 family: **gpt-5.6-sol** (frontier) only for the Orchestrator, whose short planning prompts keep Sol's premium bounded; **gpt-5.6-terra** (balanced) for every agent that synthesises heterogeneous evidence, renders binding judgements, or interprets structured tool output against a regulatory rubric — including the Verifier, which at ~68 % of pipeline tokens is the cost driver and prices out Sol; **gpt-5.6-luna** (cost-efficient) for bounded interpretation, retrieval, and small-context lookups. No agent uses OpenAI's **Flex** processing tier any more: Sol and Terra reject the `service_tier` parameter, and the two Luna agents stay on the default tier because their many short calls sit on the audit's latency path (`AAA_DISABLE_FLEX` remains as a global kill-switch, and `flex_retry` remains for explicit Luna overrides). LiteLLM keeps any of these swappable for an Anthropic Claude, DeepSeek, Mistral, or local Ollama equivalent via the `LITELLM_MODEL_*` overrides in `aaa/settings/`.

**Provider switch (`PROVIDER`).** The whole roster can be redirected without touching agent code. `PROVIDER=nvidia` resolves through `nvidia_roster.py` (NVIDIA NIM, `build.nvidia.com`) and propagates `NVIDIA_API_KEY` into the `NVIDIA_NIM_API_KEY` name LiteLLM's `nvidia_nim/` prefix reads; `PROVIDER=openrouter` resolves through `openrouter/roster.py` and needs no aliasing, since LiteLLM's `openrouter/` prefix reads `OPENROUTER_API_KEY` directly. Anything unrecognised falls back to the GPT-5.6 registry. **`PROVIDER=openrouter` is what this repo's `.env` ships since 2026-09-09**: NVIDIA NIM's free tier exhausted mid-engagement that day — 34 of 54 calls degraded through `429` → `503` → `404`, and the run produced a report whose every narrative section had fallen back to deterministic assembly — while the same roster model answered a probe over OpenRouter in 14 s against NIM's 100–500 s per call. Both routes serve the identical model; `nvidia` remains supported as the fallback. The NIM side is **no longer three-tier**:

| Tier | OpenAI (default) | NVIDIA NIM (`PROVIDER=nvidia`) | OpenRouter (`PROVIDER=openrouter`) |
|---|---|---|---|
| Sol — frontier | `gpt-5.6-sol` | `nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b` | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` |
| Terra — workhorse | `gpt-5.6-terra` | `nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b` | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` |
| Luna — bounded / retrieval | `gpt-5.6-luna` | `nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b` | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` |

**OpenRouter is an alternative route, not a substitute for full runs.** Its published caps on `:free` model variants are 20 requests per minute, and 50 per day on an account that has never purchased credits (1000/day once $10 has been bought at any point, and the higher floor persists if the balance later drops). `aaa/platform/rate_limit/` throttles the per-minute cap; the daily one is deliberately *not* implemented, because a limiter can smooth a per-minute cap by sleeping seconds whereas waiting out a daily quota would stall an audit for hours — exceeding it must surface as the provider's own 429. One mock engagement costs roughly 30–60 LLM calls, so an unfunded account cannot complete a single case. `context_window` is declared as 1,000,000 for the `:free` route, which advertises a larger window than the same model's paid variant (512,288). Being an aggregator, OpenRouter serves one slug from potentially several upstream providers at different quantizations — the reason the Stage B provenance contract (§6.3) asks customers on OpenRouter to record `upstream_provider` alongside the slug.

The NIM tiers collapsed onto one model on 2026-08-15. The previous split (`deepseek-v4-pro` / `deepseek-v4-flash` / `nemotron-3-nano-30b-a3b`) broke when both DeepSeek models reached end of life on 2026-08-07 and began returning `410 Gone`, which silently fell every agent back to its deterministic path — runs still exited 0 while reporting `0 ok, 4 error`. Applying Nemotron 3 Ultra (550B Latent-MoE, 55B active) to all fourteen agents trades throughput for uniform quality on a free-tier account. Reasoning is **on by default** across the Nemotron 3 family, costing roughly 3–4× the output tokens and up to an order of magnitude more latency per call; `chat_template_kwargs: {"enable_thinking": false}` disables it but is not currently plumbed through `ModelConfig`. `ModelConfig.context_window` is declared as `262144` — NVIDIA publishes "up to 1M tokens" for the family, but their own serving configuration defaults to 256K and requires an explicit opt-in flag to exceed it, and sizing a token budget against capacity the endpoint does not offer is worse than the honest figure.

No NIM agent carries a `service_tier` — the OpenAI-compatible endpoint has no Flex equivalent. Two cautions for roster changes, both learned the hard way. A model appearing in the NIM catalogue is not proof of account access: `nvidia/llama-3.1-nemotron-ultra-253b-v1` lists but returns `404 Function not found for account`, so candidates must be probed against the target account. And an unversioned model id is not a stable dependency: `deepseek-v4-flash` was withdrawn while the dated snapshot `deepseek-v4-flash-0731` stayed live — the same unpinned-alias failure the Stage B provenance contract (§6.3) now requires *customers* to avoid. For the same reason, tests must assert against `NVIDIA_AGENT_MODELS` rather than a literal model id. `aaa/platform/rate_limit/` throttles NIM calls against free-tier caps; sustained load still returns `Service temporarily overloaded`, which degrades the affected artefact to its deterministic fallback rather than failing the audit.

### 3.1 Tier 1 — Cross-Cutting Services (always-on)

| # | Agent | Model | Primary responsibility |
|---|-------|-------|------------------------|
| 1 | **Orchestrator** | **gpt-5.6-sol** | Owns the audit plan, runs the python-constraint CSP, sequences phases, spawns/monitors subagents, decides parallel vs sequential dispatch. |
| 2 | **Verifier** | **gpt-5.6-terra** | Independent critic: judges every phase artefact against a rubric (factual accuracy, completeness, evidence linkage, regulatory citation correctness) before the Orchestrator admits it to the compliance matrix. |
| 3 | **Regulatory RAG** | **gpt-5.6-luna** | Answers "what does Art. X §Y require?" on demand. Indexes the EU AI Act, GDPR, ISO/IEC 42001, ISAE 3000, and ISO 19011 corpus; phase agents also combine this with per-engagement client-document search where available. |

### 3.2 Tier 2 — Phase Agents (one per engagement)

| # | Agent | Model | UAGF-TAM phase | Primary responsibility |
|---|-------|-------|----------------|------------------------|
| 4 | **Phase 1 — Scope (Declaration Verifier)** | **gpt-5.6-terra** | P1 | **Verifies** the Stage-A triage declaration (modality, risk tier, Annex III sections, deployment context) collected at intake (§6 Stage 0); enforces the Art. 5 prohibition gate; performs GPAI screening; emits the `declaration_verification` map (match / mismatch / corrected). The `is_llm_or_agentic` flag is taken from the client declaration and only overridden if Phase 1 detects a verified mismatch (which raises HITL per §8.4). |
| 5 | **Phase 2 — Data Governance Auditor** | **gpt-5.6-terra** | P2 | **Loads the real training/evaluation dataset** (`artifact_loader`) and re-runs data-quality / missingness / class-balance / special-category-data scans on it; diffs the declared dataset description against the actual data; datasheet validation (Art. 10). A dataset that cannot be loaded → INSUFFICIENT_EVIDENCE, never PASS. |
| 6 | **Phase 3 — Model Validation Agent** | **gpt-5.6-terra** | P3 | **Loads the real model artefact + evaluation set** (`eval_inputs.load_scored_evaluation`), independently re-computes performance metrics, explainability (SHAP/Grad-CAM), and robustness, then `declaration_diff`s the computed metrics against the declared `accuracy_metrics` (Art. 13, 15). A non-executable / unscoreable model → material finding + INSUFFICIENT_EVIDENCE. |
| 7 | **Phase 4 — Output Fairness Tester** | **gpt-5.6-luna** | P4 | **Scores the real model** on the eval set and runs the fairness suite (demographic parity / equal opportunity / disparate impact / subgroup) **per declared-or-inferred protected attribute**; a failing group → material FAIL; unscoreable → INSUFFICIENT_EVIDENCE. |
| 8 | **Phase 5 — Governance Agent** | **gpt-5.6-terra** | P5 | Ingests `uagf_cgsa_aaa_schema.json` from the upstream S4 CGSA and **treats it as a claim to test**: `_reconcile_cgsa` checks the self-assessment's internal consistency (e.g. controls-assessed vs controls-detailed, below-threshold controls named) and lifts `blocking_findings` / `remediation_roadmap`. If the CGSA is unretrievable, governance articles are marked INSUFFICIENT_EVIDENCE (not FAIL). |
| 9 | **Phase 6 — Report Architect** | **gpt-5.6-terra** | P6 | Composes T17/T18, synthesises the executive summary, builds the formal auditor opinion, emits management-response shells, renders risk heat-map + maturity radar assets, and persists the final PDF/JSON report outputs. |

### 3.2a Evidence-Grounded Verdicts (the "real auditor" model)

The pipeline is built on one rule: **absence of evidence is never `PASS`.** The audit
independently re-derives every quantitative claim and grounds every article verdict in
traceable evidence rather than admitting artefacts by default.

- **Independent re-computation.** Phase agents load the *real* client artefacts referenced
  in Stage B (`model_artifact_uri`, `evaluation_dataset_uri`, `training_dataset_uri`) and
  re-run the analysis tools on them. Declared `accuracy_metrics` are `declaration_diff`'d
  against the recomputed values; a material gap is a finding. Supporting modules:
  `aaa/platform/artifact_loader/` (resolves a store URI to a model/CSV/docx, raising
  `ArtifactUnavailable` rather than returning a silent stub), `aaa/tools/eval_inputs/`
  (`load_scored_evaluation`, shared by Phases 3 & 4), `aaa/tools/data_dictionary/`
  (target / positive-label / sensitive-column resolution), and `aaa/tools/findings/`
  (canonical finding dicts).
- **The Verifier gate is enforced, not aspirational.** Every phase artefact is critiqued by
  the independent Verifier via `aaa/agents/tier1/phases/verification.py::run_phase_with_verification`
  before admission; a `rerun` re-dispatches the phase agent (bounded by `MAX_RERUNS`), an
  `escalate_hitl` flags the engagement. (Previously the critiques were hardcoded to
  `accept`.)
- **Verdict ladder** (`aaa/agents/tier1/phases/compliance_matrix/`): per article —
  a confirmed material finding → `FAIL`; required analysis not performed
  (`insufficient_evidence_articles`) → `INSUFFICIENT_EVIDENCE`; a possibly-material /
  observation finding → `PASS_WITH_OBSERVATIONS`; admitted, verifier-accepted, no findings →
  `PASS`. Each row carries `article_evidence` (rationale + evidence URIs + supporting
  template ids + CGSA control ids). The final verdict is `FAIL` if any article FAILs (or the
  CGSA is present and reports `csp_satisfiable=false` / `phase5_verdict=FAIL`); otherwise
  `PASS_WITH_OBSERVATIONS` when any article is `INSUFFICIENT_EVIDENCE` or
  `PASS_WITH_OBSERVATIONS`; else `PASS`.
- **Auditor opinion** (ISAE 3000 style): `unqualified` (clean PASS, no material findings),
  `qualified` (PASS_WITH_OBSERVATIONS), `adverse` (FAIL), or `disclaimer_of_opinion` — set
  via `opinion_disclaimer` when a *mandatory high-risk* article (Art. 9/10/11/12/13/14/15/17)
  is `INSUFFICIENT_EVIDENCE`, i.e. conformity cannot be concluded.

- **Scope limitations — the audit programme** (`aaa/platform/audit_programme/`). A procedure
  that could not be performed is a *scope limitation* (ISAE 3000 (Revised); ISA 500 —
  sufficient appropriate evidence; ISA 705 — modifications for an inability to obtain it),
  and it is decided from what ran, never from an agent's self-reported confidence. Each
  phase records `procedure_outcomes` (`performed` / `not_performed` + reason) in its
  delta; `apply_audit_programme` runs at the start of verdict derivation against a fixed
  programme that maps every procedure to an article element and marks it *sufficient*
  (can supply the element's evidence alone) or *supplementary*:

  | Procedure | Phase | Article · element | Kind |
  |---|---|---|---|
  | `metric_suite` | P3 | Art. 15 · accuracy | sufficient |
  | `golden_set_evaluation` | L | Art. 15 · accuracy | sufficient |
  | `robustness_probe` | P3 | Art. 15 · robustness | sufficient |
  | `prompt_injection_suite` | L | Art. 15 · cybersecurity | sufficient |
  | `specialist_adversarial_probe` | Cyber | Art. 15 · cybersecurity | supplementary |
  | `pii_deep_dive` | Privacy | Art. 10 · special-category data | supplementary |

  An element whose sufficient procedures all have outcomes and none was performed adds its
  article to `insufficient_evidence_articles` (→ `INSUFFICIENT_EVIDENCE`); a covering
  sufficient procedure keeps the evidence (the golden set did not run, Phase 3 recomputed
  accuracy). A supplementary procedure not performed changes no verdict and is disclosed.
  Every limitation, with its effect, is written to `scope_limitations`, to
  `run_integrity.scope_limitations`, and into the opinion's scope paragraph. Tier-3
  confidence (0.6 when the specialist tool did not run) stays descriptive.
- **Nonconformity grading — T15 Art. 12 / Art. 72** (`aaa/agents/tier2/governance_agent/t15/grading/`).
  Graded as conformity assessment grades findings (ISO/IEC 17021-1 §3.12–3.13, ISO 19011): a
  required element absent or not shown operating is a *major* nonconformity → `FAIL`; a
  partial lapse is *minor* → `PASS_WITH_OBSERVATIONS`; every element evidenced → `PASS`.
  Art. 72's essential elements, from Art. 72(1)–(2) and Art. 73: performance monitoring
  (accuracy or drift), non-discrimination monitoring, data from deployers and affected
  persons, and a serious-incident process. Each is read from quoted document passages as
  *operating*, *documented*, *declared absent*, *not shown operating* (the provider declares
  its monitoring largely unbuilt, so a documented element is a specification, not a
  system) or *not evidenced*; sources combine so that positive evidence establishes an
  element and a stated absence outweighs silence. No plan or measures at all → `FAIL`.
  Art. 12: no logging documented → `FAIL`; a declared gap in recording the system's
  outputs (inference, prediction, decision, rank) → `FAIL`, because risk situations cannot
  be reconstructed (Art. 12(2)); any other declared logging gap → `PASS_WITH_OBSERVATIONS`.
  The rationale names every element with its quote; the Verifier reviews the grade and
  does not decide it.
- **Unmeasured is null, never a default.** A model or data test that did not measure a
  value reports `null`, and narratives print "not measured". No tool substitutes a
  model-free proxy for a model-based technique (SHAP, LIME and Grad-CAM return nothing
  and their reason when they cannot run on the model); no empty-input stub reports
  0 % missing, "no imbalance", "no PII" or a 0.0 rate; a column-name PII screen claims
  no cell counts and no absence; a keyword toxicity screen writes no score and leaves a
  hit-free sample `NOT_TESTED`; an empty or undefined cohort has no confidence interval.
  Outlier detectors are scored in the dataset's label space (−1/+1 mapped through the
  declared positive label) and metrics follow the task, so a detector or forecaster is
  not measured as something it is not. `tests/unit/test_no_default_numbers_leak.py`
  probes every tool with no evidence and fails on any number it still returns. The same
  rule holds where results are displayed: an engagement bound by no article has no
  conformity score (`article_score` → `None`; the gauge and tiles say no requirement
  applies instead of `0/100` and `0/0`), and an absent KPI prints "not measured" on the
  PDF cover rather than `0.00`. T09's known limitations are measured too: a missed declared
  target, and the evaluation sample size with the worst-case 95% margin of a rate measured on
  it — never a fixed metric threshold, and never "no limitations" because no check fired.
- **A declared field is about what its name says.** Datasheet (T06) questions require a
  passage to be about the dataset Phase 2 measured; a sentence of the declared
  `training_data_description` is about the training data whatever the provider calls it
  ("screening corpus"), while an uploaded document must name the dataset (`Question.subject`
  / `subject_fields`).
- **Judgements rest on an interval or a declaration, never a constant.** A declared metric is
  corroborated when it lies inside the measured metric's 95% percentile bootstrap interval on the
  evaluation rows (1,000 seeded resamples; above it is a material overclaim, below it an
  observation). Robustness noise is a fraction of each feature's own standard deviation on a
  seeded row sample; a probe establishes degradation when the paired bootstrap interval of the
  accuracy drop excludes zero, and a declared `adversarial_accuracy_<kind>_<level>` is judged
  against the probe that measures that kind at that level (overstated → FAIL). The L-branch and
  cyber verdicts compare RAGAs scores with the provider's declared targets and a declared
  injection-resistance rate with the Wilson interval of the attacks actually run. No 0.05/0.10/
  0.50/0.70/0.85 threshold decides a verdict.
- **Fairness is decided pairwise by interval, with no minimum cohort size.** Every pair of
  cohorts is compared (or each against a declared privileged cohort) at 95% held across the
  pairs (Bonferroni), because the reported pair is chosen after seeing the rates. A selection-rate
  ratio is adverse (`FAIL`) when a pair's Katz interval lies wholly below four-fifths — the one
  comparator with a regulatory source (29 CFR §1607.4(D)) — conforming (`PASS`) when every
  pair's lies at or above it, and otherwise `INSUFFICIENT_EVIDENCE`. Demographic-parity,
  equal-opportunity and subgroup-accuracy differences have no sourced tolerance: an established
  difference (Newcombe interval excluding zero) is an observation. The Phase 2 label examination
  uses the same rule (adverse → possibly-material finding, undecided → observation). The former
  30-row floor and the 0.10/0.20/0.60 bands are gone; a small cohort yields a wide interval,
  not a refusal, and cannot veto a pair that decides.
- **A summary of deterministic checks is deterministic.** T02's `phase1_summary` and T14's
  `phase5_narrative_summary` are built from the artefact's own fields (or the CGSA partner's
  narrative); the LLM's prose feeds the phase Report, not the artefact, because a retelling can
  contradict the fields beside it. The T07 narrative says whether any tool measured anything.
- **Evaluation judges run on the run's own route and within its budget.** RAGAs and TruLens use
  the UAGF-TAM-L roster model of the active provider (free on OpenRouter), not a library default;
  their calls bypass the LLM audit log, so a default model would go unseen. The RAGAs evaluation
  is awaited under the L-branch's remaining budget and its job tasks are cancelled at the
  deadline, recording `computed: false` with the reason instead of losing the branch. The
  golden set is measured on as many seeded-random samples as that budget allows, batch by batch;
  `ragas_metrics` carries the means, `sample_size`, `population_size` and 95% bootstrap
  `intervals`, and a declared RAGAs target is missed only when the interval lies below it.
- **The Verifier judges the artefact; what the artefact records about the provider judges the
  article.** Every Verifier issue has an `issue_type`: an `artefact_defect` (the artefact is
  wrong) can force a rerun or escalation and is the only kind the admission gate reads; an
  `evidence_gap` (the provider did not supply or document something) and a
  `provider_nonconformity` (the provider falls short) do not reject an accurate artefact. At phase
  close they become findings on the admitted artefact's articles
  (`verification/provider_findings`): a material non-conformity fails the article, a material gap
  records it INSUFFICIENT_EVIDENCE, a possibly-material one is an observation — so admitting the
  artefact can never turn a gap into a PASS.
- **Metrics measure what the provider claims.** For a binary target the positive class's
  precision, recall, F1, FPR and FNR are computed; F1 is the headline metric when that
  class is the minority (accuracy would reward never predicting it). A declared
  `f1_score` is compared with the positive-class F1, and declared `target_fnr` /
  `target_fpr` are checked as upper bounds (`model_validator/targets.py`). T09 records
  the loaded model's own input/output shape, parameter count (where defined) and
  hyperparameters (`tools/model_meta/introspect`).
- **Narratives about measurements come from their artefact's fields.** The LLM's reply
  summarises the whole phase and stays the Report summary; it no longer replaces the
  T07, T11 or T12 narrative, where it quoted numbers those artefacts do not hold.
- **A FAIL names what decides it.** Rationales list material findings first so the length
  clip can only drop qualifying ones; a governance finding is cited by its control id,
  and a FAIL resting on the provider's self-assessment says so rather than "independent
  analysis".

### 3.3 Tier 3 — Specialist Sub-Agents (on-demand)

Tier-3 agents are required to satisfy Mökander 2023's **application-layer audit** obligations and Falco 2021's **independent security review** principle. Each is spawned only when its triggering condition fires, so steady-state token cost is bounded.

| # | Agent | Model | Triggered by | Primary responsibility | Academic justification |
|---|-------|-------|--------------|------------------------|------------------------|
| 10 | **UAGF-TAM-L Branch Agent** | **gpt-5.6-terra** | Phase 1 sets `is_llm_or_agentic = true` | Replaces Phases 2–4 with golden-set evaluation, faithfulness/grounding tests, prompt-injection & jailbreak suites, tool-call trajectory audit for agentic systems. | Mökander 2023 §4 (LLM-specific audit layer); exposé §2 Phase 1 UAGF-TAM-L requirement |
| 11 | **Cybersecurity Sub-Agent** | **gpt-5.6-terra** | Phase 5 when Art. 15 evidence is missing **or** risk tier = high **or** Cyber red-flag in any phase artefact | Adversarial robustness (FGSM/PGD on CV, injection on LLM), sandbox-escape probes for agentic systems. | EU AI Act Art. 15 (accuracy, robustness, cybersecurity); Falco 2021 (independent security audit) |
| 12 | **Privacy / DPO Sub-Agent** | **gpt-5.6-terra** | Phase 5 when GDPR overlap detected (special-category data, biometric data, Annex III §1 use case) | Art. 10 §5 lawful-basis check, DPIA cross-reference, retention & minimisation review. | EU AI Act Art. 10 §5; GDPR Art. 35 (DPIA); Mökander 2023 application-layer privacy audit |
| 13 | **DocIntelligenceAgent** | **gpt-5.6-terra** (default tier) | Stage 0 — **no longer called by the wizard**; reachable via `POST /api/v1/engagements/{id}/extract-triage` | Ingests customer-uploaded artefacts into the per-engagement Qdrant collection (`client_doc_ingest`), issues per-field vector searches (`client_doc_search`), and calls the LLM in a single batched extraction to pre-populate Stage A / Stage B fields. Returns a `DocExtractionResult` (field values + confidence scores + source attribution). The wizard dropped the extraction half — it indexes uploads through `ingest_documents()` and the customer fills the review form — because `extraction_result` only ever seeded widget defaults, while the ingest is load-bearing. The endpoint is unchanged for callers that want pre-fill. Non-interactive agents stalled by the Flex `429 Resource Unavailable` risk would block the user mid-wizard, so this agent stays on the default tier. | §6 Stage 0 UX redesign; EU AI Act Art. 11 (intake quality); user-experience best practice (agent-assisted form fill) |
| 14 | **ClientBrief** | **gpt-5.6-terra** | End of Phase 6, after the ReportArchitect's T18 is applied to the state | Writes `T19_client_brief` — the plain-language brief the audited organisation reads, one LLM call per audited article plus one for the opening. Each call receives that article's evidence bundle (intake declarations and the audit's verification of them, admitted artefact payloads resolved from the store, the artefacts the Verifier rejected and its stated reasons, the findings, the CGSA controls, and the retrieved regulatory passages) and returns the declared-versus-observed contrast that produced the verdict. Verdicts, counts and the matrix table are rendered from `AuditState`, never from the reply, so no wording can move a FAIL. A failed call falls back to a deterministic section built from the bundle and is marked as such. | Mökander 2023 §5 (audit findings must be actionable by the audited party); ISAE 3000 (Revised) ¶A62 — communication with the engaging party |

**Why these three are non-negotiable for quality.** The exposé's required deliverable is *"EU AI Act-compliant"* reports (line 82). Compliance with Articles 10 §5, 15, and the GPAI/LLM evidentiary obligations cannot be discharged by the six phase agents alone without violating the Mökander/Falco independence principle: the agent that wrote the artefact cannot also be the agent that adversarially tests it. Removing any Tier-3 agent would either (a) leave a regulatory article unaudited, or (b) collapse audit and adversarial review into the same agent. Both are documented quality regressions.

### 3.1a Regulatory Corpus — Ingestion Design

The Regulatory RAG agent's knowledge base is built by the `scripts/ingest_regulatory_corpus/` package (run once via `python -m scripts.ingest_regulatory_corpus`), which populates two Qdrant collections. **LlamaIndex appears here and only here**: its `SentenceSplitter` chunks each structural unit at ingestion time (`chunker.py`), so chunks never cross a legal boundary. Retrieval itself does not go through LlamaIndex — `RegulatoryRAG` queries Qdrant directly (dense + sparse, fused via RRF), with a built-in KB fallback. Fusion returns a candidate pool (`rerank.CANDIDATE_POOL`, 15) rather than the caller's `top_k`, and a local cross-encoder (`fastembed`, no network call) then reads each candidate against the query and keeps the best `top_k`, annotated with `retrieval_score`/`rerank_score`/`relevant`. RRF compares query and chunk only through separately-embedded vectors, so nothing had judged whether a surviving chunk was on point, and a passage ranked just outside `top_k` was unreachable. The re-ranker selects and orders; it never edits chunk text, so what an agent quotes is the corpus verbatim. It fails soft to the RRF order, and candidates it passes over are logged with their scores. Its loaders/parsers follow the same module/sub-module/file convention as `aaa/` — the compliance-checker lookup, ISO/IEC 42001 loader, and low-level PDF helpers live in the `checker/`, `iso/`, and `pdf/` subpackages respectively.

**Corpus (as of latest ingestion)**

| Regulation | Source format | Chunks | Notes |
|---|---|---|---|
| EU AI Act (Regulation (EU) 2024/1689) | EUR-Lex HTML | **339** (136 articles, 181 recitals, 22 annexes) | BeautifulSoup HTML parser |
| GDPR (Regulation (EU) 2016/679) | EUR-Lex HTML | **288** (115 articles, 173 recitals) | BeautifulSoup HTML parser |
| ISO/IEC 42001:2023 | PDF | **88** (32 clauses §4–§10, 56 Annex A controls) | `pypdfium2` PDF backend (see below) |
| ISAE 3000 (Revised) | PDF (IAASB) | **411** (251 numbered paragraphs, 160 application-material paragraphs) | `pypdfium2` PDF backend + paragraph segmentation |
| ISO 19011:2018 | PDF | **74** (56 clauses, 18 Annex A controls) | `pypdfium2` PDF backend |
| **Total** | | **1200** corpus chunks | |

`obligations_index` additionally holds **15** obligation-question points from the compliance-checker JSON.

**PDF parsing strategy for ISO/IEC 42001**

ISO/IEC 42001:2023 is published using PDF Tools AG's toolchain, which emits newline-separated cross-reference tokens (e.g. `1\n0\nobj` instead of `1 0 obj`). The `pdfminer.six` / `pdfplumber` stack cannot parse this format and returns 0 pages without raising an exception. The ingestion script therefore uses **`pypdfium2`** (`>=5.8.0`) as its PDF backend, which reads the file correctly.

In addition, ISO 42001 frequently places a clause or Annex A control number on its own line with the title on the next line (split-line headings, e.g. `A.10.3` then `Data minimisation`). Three regular expressions handle this:

- `_ISO_CLAUSE_NUM_RE` — matches a bare clause number (e.g. `4.1`).
- `_ISO_CONTROL_NUM_RE` — matches a bare Annex A control number (e.g. `A.6.2`).
- `_ISO_TITLE_HEAD_RE` — matches a combined `<number> <title>` heading on one line.

When a bare numeric line is detected, the parser looks ahead to consume the next non-blank line as the title.

**Idempotency**

Each chunk's Qdrant point ID is a deterministic **SHA-256** of `text + regulation + ref + chunk_index`. `_fetch_existing_ids()` scrolls the collection before any embedding call and filters out already-present IDs. Re-running the ingestion script produces **zero OpenAI API calls** when the corpus is unchanged.

---

### 3.4 Org Chart

```mermaid
flowchart TD
    classDef high fill:#5b6cff,stroke:#2a3aad,color:#ffffff,stroke-width:1px
    classDef mid fill:#7fb069,stroke:#3f6a32,color:#0b1f08,stroke-width:1px
    classDef low fill:#f4c95d,stroke:#8a6a14,color:#2a1f06,stroke-width:1px
    classDef tier fill:#eef0f5,stroke:#6b7280,color:#111827,stroke-width:1px,stroke-dasharray:4 3

    T1[Tier 1 · Cross-Cutting]:::tier
    T2[Tier 2 · Phase Agents]:::tier
    T3[Tier 3 · Specialists]:::tier

    A1["1 · Orchestrator<br/>gpt-5.6-sol"]:::high
    A2["2 · Verifier<br/>gpt-5.6-terra"]:::high
    A3["3 · Regulatory RAG<br/>gpt-5.6-luna"]:::low

    A4["4 · Phase 1 · Scope / Risk Classifier<br/>gpt-5.6-terra"]:::mid
    A5["5 · Phase 2 · Data Governance Auditor<br/>gpt-5.6-terra"]:::mid
    A6["6 · Phase 3 · Model Validation<br/>gpt-5.6-terra"]:::high
    A7["7 · Phase 4 · Output Fairness Tester<br/>gpt-5.6-luna"]:::low
    A8["8 · Phase 5 · Governance Agent<br/>gpt-5.6-terra"]:::high
    A9["9 · Phase 6 · Report Architect<br/>gpt-5.6-terra"]:::mid

    A10["10 · UAGF-TAM-L Branch<br/>gpt-5.6-terra"]:::high
    A11["11 · Cybersecurity Sub-Agent<br/>gpt-5.6-terra"]:::mid
    A12["12 · Privacy / DPO Sub-Agent<br/>gpt-5.6-terra"]:::mid

    T1 --- A1 & A2 & A3
    A1 --> T2
    T2 --- A4 & A5 & A6 & A7 & A8 & A9
    A4 -. routes LLM/agentic .-> A10
    A8 -. on-demand .-> T3
    T3 --- A10 & A11 & A12
```

### 3.5 Article 43 — Conformity Assessment Procedure Selection

Article 43 of Regulation (EU) 2024/1689 obliges the provider of a high-risk AI system to establish its conformity-assessment procedure **before** placing the system on the market. The Article has three paragraphs and they route to three different answers: §1 governs Annex III **point 1** (biometrics), §2 governs Annex III **points 2 to 8**, and §3 defers to the sectoral regime for products covered by the Union harmonisation legislation in **Annex I Section A**. The AAA Orchestrator must make the choice explicit in every audit report; it determines the report template and the downstream regulatory filings.

| Procedure | Annex | When required | AAA report section |
|---|---|---|---|
| **Internal control** | **Annex VI** | (a) Annex III **points 2–8** — Art. 43 §2 assigns this unconditionally, and it "does not provide for the involvement of a notified body", so neither the harmonised-standards test nor a provider election can move it; **or** (b) Annex III **point 1** where harmonised standards *have* been applied and the provider has not elected Annex VII (Art. 43 §1(a)) | "Article 43 § Procedure" → Annex VI declaration + technical-documentation index (Annex IV) |
| **Third-party assessment (notified body)** | **Annex VII** | Annex III **point 1** only: (a) harmonised standards / common specifications not applied, or applied only in part — Art. 43 §1 second subparagraph makes Annex VII mandatory; **or** (b) the provider has elected it under Art. 43 §1(b) | "Article 43 § Procedure" → Annex VII notified-body section + conformity certificate placeholder |
| **Sectoral procedure** | **Annex I Section A act** | The system is covered by Union harmonisation legislation listed in Annex I Section A. Art. 43 §3: the provider follows the procedure *that act* requires, and the Section 2 requirements are assessed as part of it. Declared at Stage A as `annex_i_section_a` (carried in state as `annex_i_section_a_acts`) | "Article 43 § Procedure" → the sectoral act cited, with the Section 2 requirements mapped into it |
| **Not applicable** | — | Limited- or minimal-risk systems; GPAI subject to Articles 51–55 separately | "Article 43 § Procedure" → "Not applicable; rationale: …" |

**Selection logic (Orchestrator, deterministic).** The `art43_select` tool (see §4.5) implements the following CSP-style rule. It runs **twice** per engagement:

1. **Preview** — at the end of Stage A intake, against the *declared* values (`declared_risk_tier`, `declared_annex_iii_sections`, `provider_elects_third_party`). The preview is shown to the client in the wizard ("If your declaration is correct, your conformity-assessment procedure will be: …") and is written to `T01a_stage_a_triage`.
2. **Final** — after Phase 1 has verified those declarations, against the *verified* values. The final decision is the binding one written to `T05_art43_decision`. If preview and final differ, the difference is recorded in `T01c_intake_completeness_report` and raised through the HITL "declaration mismatch" trigger (§8.4).

```python
def select_art43_procedure(state: AuditState) -> Art43Decision:
    if state.risk_tier in {"minimal", "limited"}:
        return not_applicable("System is not high-risk per Art. 6 / Annex III.")
    if state.risk_tier == "gpai":
        return not_applicable("GPAI obligations governed by Arts. 51–55, not Art. 43.")
    if state.risk_tier == "prohibited":
        return not_applicable("Art. 5 prohibition; engagement halted.")

    # Art. 43 §3 first: its subject is the product, not the use case, and the
    # procedure it names is neither Annex VI nor Annex VII.
    if state.annex_i_section_a_acts:
        return Art43Decision(procedure="annex_i_sectoral",
                             rationale=f"Covered by Annex I Section A: {cite_acts(...)}. "
                                       "Art. 43 §3 defers to that act's procedure.")

    # Art. 43 §1 — Annex III point 1 (biometrics) only.
    if any(e.annex_iii_section == "1" for e in state.annex_iii_mapping):
        if not state.harmonised_standards_applied:      # set by Phase 5, from the CGSA
            return Art43Decision(procedure="annex_vii_notified_body",
                                 rationale="… second subparagraph of Art. 43 §1 …")
        return Art43Decision(
            procedure=("annex_vii_notified_body" if state.provider_elects_third_party
                       else "annex_vi_internal_control"),
            rationale="… Art. 43 §1(b) …" if state.provider_elects_third_party
                      else "… Art. 43 §1(a) …")

    # Art. 43 §2 — Annex III points 2 to 8, unconditional.
    return Art43Decision(procedure="annex_vi_internal_control",
                         rationale="Annex III points 2 to 8; Art. 43 §2 assigns internal "
                                   "control based on Annex VI, which does not provide for "
                                   "the involvement of a notified body.")
```

Every rationale is derived from the branch that produced it — no branch asserts a
condition it did not test. The rule table previously returned one fixed string on
its fall-through ("harmonised standards applied in full") for a paragraph that
imposes no such condition, which put a false statement into every binding
statement the system wrote; see the case 06 addendum, findings M9/M10.

**Ordering caveat.** `harmonised_standards_applied` is set by Phase 5 from the
CGSA, and `T05_art43_decision` is written by Phase 1 — so Phase 1 decides on a
value it cannot yet have. `node_compliance_matrix` recomputes the decision from
the completed state, and `compliance_matrix.art43_restatement.reconcile_art43`
raises a **material** finding if the two disagree rather than leaving a stale
artefact beside a fresher state field.

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
| `drift_test` | in-repo PSI (`aaa/tools/drift_test`) | Phase 2 — training-vs-evaluation distribution shift; identifier / free-text columns are skipped as `not_comparable` |
| `pii_scan` | Presidio | Phase 2, Privacy Sub-Agent — an entity that cannot name a GDPR Art. 9 category (NRP: nationality, religious or political group, which spaCy also gives to language names) adds no category; it is kept under `unresolved_mentions` with its matched terms |

### 4.2 Model & Explainability Tools

| Tool | Library | Used by |
|------|---------|---------|
| `metric_suite` | scikit-learn (`compute/sklearn.py`), pure-Python fallback (`compute/python.py`) | Phase 3 |
| `shap_explain` | shap | Phase 3 |
| `gradcam_explain` | pytorch-grad-cam | Phase 3 (CV models) |
| `lime_explain` | lime | Phase 3 |
| `text_explain` | in-repo (`aaa/tools/text_explain`) | Phase 3 (NLP) — \|coef\|-ranked token importances from a TF-IDF + linear pipeline, and exact per-instance token contributions (tf-idf weight × coefficient; with the intercept they sum to the decision score) for T10's local explanations |
| `robustness_probe` | in-repo (Gaussian noise; character-level typo noise for `nlp`) | Phase 3, Cyber Sub-Agent |

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
| `prompt_injection_suite` | garak, promptfoo *(neither installed — see below)* | UAGF-TAM-L, Cyber |
| `trajectory_audit` | custom (Langfuse traces) | UAGF-TAM-L |
| `toxicity_classifier` | detoxify | UAGF-TAM-L, Phase 4 |

**What these tools do when their library is absent — and what they must never
do.** `ragas_eval` and `groundedness_check` report `computed: false` with a
reason and null metrics. `prompt_injection_suite` has no adversarial back end
wired: garak is not installed and no engagement has yet supplied a
`stage_c.read_only_api_endpoint` to probe, so it raises
`InjectionProbeUnavailableError` and returns `tested: false` with a null
`vulnerability_rate`, or — when a system prompt *was* supplied — a **labelled**
`static_prompt_analysis` that reads the real artefact and counts zero probes.

A null is not a zero. `vulnerability_rate: 0.0` reads as "probed and clean";
`null` means nothing was probed, and `derive_verdict` treats it as a missing
measurement rather than a pass or a fail. This matters because the opposite was
shipped: `_run_garak` returned a hardcoded 150 probes, 2 successful attacks, a
1.3 % rate and a named finding on every call for every engagement, and that
invented result reached the narrative LLM, T16, the client report and a FAIL
gate. The T16 schema could not express "not tested" — `additionalProperties:
false` around a required numeric rate — which is what allowed it; the schema now
carries `tested`, `method` and `not_tested_reason`.

### 4.5 Governance & Reporting Tools

| Tool | Library | Used by |
|------|---------|---------|
| `csp_solver` | python-constraint | Orchestrator (phase-routing CSP, §6.2) |
| `schema_validate` | jsonschema | Phase 5 (S4 payload), Phase 6 (final report JSON) |
| `cgsa_pull` | custom (HTTP client; pulls `uagf_cgsa_aaa_schema.json` from S4) | Phase 5 |
| `cgsa_ingest` | custom (parses + validates the pulled CGSA payload) | Phase 5 |
| `annex_iii_classify` | custom — blends `RegulatoryRAG.search` similarity (0.6) with keyword overlap (0.4) over the Annex III catalogue + rule table §3.6; keyword-only when no RAG function is supplied | Phase 1 |
| `art43_select` | custom (deterministic rule §3.5) | matrix assembly (run for the Orchestrator by the loop) |
| `regulatory_search` | `RegulatoryRAG.search()` — Qdrant hybrid, built-in KB fallback. Not an `aaa/tools` module: agents receive hits pre-seeded, or request more via a `retrieval_plan` field | Regulatory RAG; all phase agents (indirect) |
| `client_doc_ingest` | custom (chunk + embed + Qdrant upsert) | Intake Validator |
| `client_doc_search` | custom (per-engagement dense retrieval) | Phase 1 / 2 / 3 / 5 |
| `template_render` | jinja2 over 20 artefact templates (§4A) | Report Architect (agents return artefact JSON; the runtime renders) |
| `report_render` | reportlab + plain-text fallback | Phase 6 |
| `risk_heatmap_render` | matplotlib | Phase 6 |
| `maturity_radar_render` | matplotlib | Phase 6 |
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
| 1b | `T01b_annex_iv_dossier` | Intake (Stage B) | Orchestrator (Intake Validator) | Structured upload of the Annex IV §1–§9 technical documentation: required text fields plus URI-backed file uploads for risk-management, declaration-of-conformity, post-market, and L-branch artefacts. Also carries optional training/evaluation dataset URIs and model artefact / metadata URIs for downstream data/model review. | **Art. 11 + Annex IV §1–§9** |
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
| 18 | `T18_audit_report` | P6 Report | Report Architect | Final Annex-IV-aligned report payload plus rendered outputs; embeds T01a–T17 and includes auditor opinion, management-response shell, remediation roadmap, heat-map/radar URIs, and rendered PDF/JSON metadata. | Art. 11, Annex IV |
| 19 | `T19_client_brief` | P6 Report | ClientBrief | The same result addressed to the audited organisation: per requirement, what the submission declared, what the evidence showed, which article the gap falls under, what is working, and what to do. Stored as Markdown and written to `data/customer/<company>/<engagement>_client_report.md`. **Not evidence** — it carries no article accountability and appears in no coverage calculation; it restates admitted findings and cannot change a verdict. | — (communication artefact) |

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
    # Independent-analysis inputs — the real artefacts Phases 2/3/4 load + re-run on.
    # All NotRequired for backward compatibility with legacy fixtures.
    model_artifact_uri: str | None         # fitted model (joblib/pickle) re-scored in Phase 3/4
    evaluation_dataset_uri: str | None     # labelled holdout re-scored for metrics + fairness
    training_dataset_uri: str | None       # re-scanned for data quality / PII (Phase 2)
    # Data dictionary — how to split X/y and scope protected-attribute fairness testing.
    # When omitted, inferred (last column = target; protected attrs from column names) and
    # the assumption is recorded as a finding (aaa/tools/data_dictionary.py).
    target_column: str | None
    positive_label: Any                    # favourable outcome for fairness (default 1)
    sensitive_feature_columns: list[str] | None
    feature_columns: list[str] | None
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
    stage_c: StageCAccess | None        # None when no live-system access is granted
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
    compliance_matrix: dict[Article, Verdict]        # Verdict ∈ PASS | PASS_WITH_OBSERVATIONS | FAIL | INSUFFICIENT_EVIDENCE | NOT_APPLICABLE | PENDING
    article_evidence: dict[Article, dict]            # per-article rationale + evidence_uris + supporting_template_ids + cgsa_control_ids + finding_ids
    blocking_findings: list[Finding]                 # accumulate-merged across phases (agent_runner)
    positive_findings: list[Finding]
    remediation_roadmap: list[RemediationItem]
    insufficient_evidence_articles: list[str]        # articles whose required independent analysis could not be performed → INSUFFICIENT_EVIDENCE
    low_confidence_phases: list[dict]                # phases closing below the 0.6 confidence floor; their articles land in the list above

    # --- verification & verdict ---
    verifier_critiques: dict[str, Critique]
    intake_completeness_score: float | None          # §9.1 KPI 0; 0.0–1.0; must be ≥ 0.80
    completeness_score: float | None                 # §9.1 KPI 1; 0.0–1.0
    regulatory_coverage_pct: float | None            # §9.1 KPI 2; 0.0–100.0
    final_verdict: Literal["PASS","PASS_WITH_OBSERVATIONS","FAIL","DISCLAIMER_OF_OPINION"] | None
    opinion_disclaimer: bool                          # true ⇒ a mandatory high-risk article is INSUFFICIENT_EVIDENCE → disclaimer of opinion
```

### 5.2 Evidence Store

Following Anthropic's pattern of writing intermediate work to the filesystem to avoid context-window blow-up:

- **Object store**: MinIO (S3-wire-compatible, AGPL-v3). The `EvidenceStore` issues the same `minio://` URI model over either backend — `EVIDENCE_BACKEND=minio` for real persistence, `memory` for process-local runs (tests, offline smoke).
- **Index**: Postgres table `evidence(engagement_id, phase, artefact_type, uri, sha256, created_at, created_by_agent)` in the target architecture; demo mode mirrors this with an in-memory metadata index.
- **Access**: Agents exchange URIs, not large blobs. `store_file(...)` supports binary-safe customer uploads, while IntakeValidator / ReportArchitect selectively pull full artefacts when ingesting client docs or rendering the final report.

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

The canonical audit flow has **twelve logical stages** (Stage 0 is now three sub-stages; Stages 4a–4c run in parallel when the Router selects the standard branch; stage 4L replaces them on the L-branch). **In production this flow is not hardcoded**: the Orchestrator model drives a ReAct loop (`aaa/agents/tier1/orchestrator/react/`) that observes the audit-state summary each turn and decides `PLAN | DISPATCH | ESCALATE_HITL | ASSEMBLE_MATRIX | FINALIZE`, with six gates enforced in code around its decisions (Art. 5 halt, intake < 0.80 Phase 1 block, per-phase dispatch cap, phase precedence, matrix-before-finalize, and a no-progress repeat guard) and every decision — including guard overrides and what the model proposed before one — recorded in `react_decision_history` for regulator replay. Exhausting the turn budget forces the outstanding mandatory phases rather than cancelling them, and records that it did so in `react_termination`. The LangGraph state machine below executes the same flow deterministically and is retained **only as the labelled offline/CI fallback** (`AAA_ORCHESTRATION_MODE=graph`, or no provider key present).

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  0. STAGE 0 — INTAKE (three mandatory sub-stages before any agent runs)      │
│                                                                              │
│  0A · Stage A — Triage                                                       │
│       Client fills the triage payload via CLI fixture, FastAPI intake, or    │
│       the Streamlit demo UI.                                                 │
│       Declares: modality, risk tier, Annex III sections, deployment context, │
│       provider_elects_third_party, GDPR overlap, GPAI flag, CGSA ID.        │
│       art43_preview computed from declared values → written to T01a.         │
│       Completeness gate: if required Stage A fields missing → wizard blocks. │
│                                                                              │
│  0B · Stage B — Annex IV Dossier Upload                                      │
│       Client uploads Annex IV §1–§9 technical documentation (structured      │
│       form + file attachments). L-branch uploads may include system prompt,  │
│       RAG manifest, guardrail config, and golden set; optional dataset/model │
│       artefacts are also captured here for downstream phase agents.          │
│       annex_iv_validator runs JSON-Schema check on submission.               │
│       intake_completeness_calculator writes T01c with intake_completeness_  │
│       score. Gate: intake_completeness_score ≥ 0.80 required to proceed.    │
│       Uploaded document URIs are ingested into client_docs_{engagement_id}   │
│       for later phase-agent retrieval when online services are available.    │
│       If score < 0.80 → wizard returns error list; client must remediate.    │
│                                                                              │
│  0C · Stage C — Scoped Live-System Access (optional, async)                  │
│       Client provides read-only API endpoint + scoped credentials via the    │
│       portal's secure vault form. Credentials stored in OpenBao; only a     │
│       secret-path reference is written to AuditState. Access scope and       │
│       expiry are constrained by the platform (§11).                          │
│       If absent (no live-system access): Phase 1 marks live-system evidence  │
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
│  7. HITL CHECKPOINT (defer, do not pause — see §8.4a)                        │
│     Escalated artefacts are recorded; the pipeline continues to Phase 6 and  │
│     emits a PROVISIONAL report + an editable hitl_review.json packet.        │
│     A human resolves it later via scripts/finalize_hitl.                     │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  8. PHASE 6 — REPORT (Report Architect Agent)                                │
│     Builds T17 + T18, auditor opinion, management-response shell, risk       │
│     heat-map, maturity radar, and rendered PDF + machine-readable JSON.      │
│     Delivered through CLI/API/UI download surfaces.                          │
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
    S2["2 · Phase 1 · Scope<br/>Declaration Verifier · gpt-5.6-terra<br/>declaration_diff → declaration_verification"]:::phase
    GATEDECL{"declaration<br/>mismatch?"}:::gate
    GATE5{"Art. 5<br/>prohibition?"}:::gate
    ROUTER{"Router<br/>is_llm_or_agentic?"}:::orch

    P2["4a · Phase 2 · Data<br/>Auditor · gpt-5.6-terra"]:::phase
    P3["4b · Phase 3 · Model<br/>Validator · gpt-5.6-terra"]:::phase
    P4["4c · Phase 4 · Output<br/>Fairness · gpt-5.6-luna"]:::phase
    PL["4L · UAGF-TAM-L<br/>Branch · gpt-5.6-terra"]:::branch

    VER{{"Verifier · gpt-5.6-terra<br/>(per-phase critic)"}}:::orch

    P5["5 · Phase 5 · Governance · gpt-5.6-terra<br/>cgsa_ingest(uagf_cgsa_aaa_schema.json)"]:::phase
    SPEC["Spawn Tier-3<br/>Cyber · gpt-5.6-terra / Privacy · gpt-5.6-terra"]:::branch

    MATRIX["6 · Compliance Matrix<br/>Orchestrator · gpt-5.6-sol<br/>art43_select (final) · intake_completeness_score"]:::orch
    HITL{"7 · HITL<br/>checkpoint?"}:::gate
    REPORT["8 · Phase 6 · Report Architect · gpt-5.6-terra<br/>T17/T18 + PDF/JSON + opinion/charts"]:::report

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
10. **Supplied evidence is examined.** After solving, a phase the catalogue marks `O` becomes `M` when the provider uploaded the evidence it tests — P2 on a training or evaluation dataset, P3 and P4 on a model *and* a dataset, UAGF-TAM-L on a golden set (`csp_solver/supplied.py`). The Orchestrator never dispatches an optional phase, so a limited-risk forecaster whose model and data were uploaded was otherwise never scored; an opinion must consider all relevant evidence obtained (ISA 330 ¶26). `S` is a routing decision and is never promoted — except Phases 3/4 of a **minimal-risk** system with a discriminative component, whose supplied model and data are examined voluntarily under Art. 95 codes of conduct; nothing binds such a system, so the matrix holds no verdict for them and their findings are restated as observations (`compliance_matrix/out_of_scope_findings.py`, which applies to every finding whose articles do not bind the engagement). The reason is recorded in `phase_plan_rationale`.
11. **Phase 1's verified tier is applied.** A declared `limited` or `minimal` tier is verified against the declared Art. 50 transparency triggers (`limited` only with one). After Phase 1, a verified tier that differs from `risk_tier` replaces it, is recorded in `risk_tier_correction`, and the phase plan is re-solved (`nodes/verified_tier.py`); before this the verified value was stored and never read.

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

### 6.3 Model Provenance — how the evaluator obtains a runnable model

Stage B originally described a model only as *a file we hold*: `model_artifact_uri` plus `model_format` / `model_framework`. That works for a tabular classifier the provider can upload, and fails for most LLM and agentic systems, where the provider runs weights they do not own — a vendor endpoint, or a base model plus a fine-tuned adapter. With nowhere truthful to record that, a dossier ends up declaring a serialisation format promising weights that never arrive. The auditor never hosts customer weights; the contract records what *identifies* a model so the evaluation service can resolve it from the vendor.

**`model_access_mode` is the discriminator.** It answers the only question a loader needs answered, and every other requirement is conditional on it:

| Mode | Meaning |
|---|---|
| `artifact_upload` | Provider uploads the weights; the bytes are in the Evidence Store. |
| `registry_reference` | Weights live in a registry; the evaluator pulls them at a pinned revision. |
| `base_plus_adapter` | A registry base model plus a fine-tuned adapter (the adapter may be uploaded; the base never is). |
| `hosted_api` | No weights exist to obtain; evaluation calls the vendor's inference endpoint. |
| `not_provided` | Nothing runnable is offered — evaluation is limited to documents, golden sets and traces, and the report says so. |

**`model_reference` is a sibling of `model_artifact_uri`, never a replacement.** The artefact URI keeps meaning "bytes we hold"; the reference means "resolve this yourself". They are kept apart because `resolve_bytes()` understands only `minio://` and `file://` — a vendor reference pushed into the URI field would fail resolution rather than route around it. The block carries the vendor identity (`provider`, `model_id`, `revision`), access facts (`endpoint_url`, `auth_type`, `gated`, `license`), the adapter layer where relevant (`base_model_id`, `base_model_revision`, `adapter_uri` ⊕ `adapter_reference`, `peft_type`), and reproducibility settings (`runtime_versions`, `quantization`, `decoding_params`).

Two fields deserve their rationale recorded. **`revision` is required**, because it is what turns a reference into evidence: `gpt-4o` and a `main` branch both re-point over time, so an audit pinned to either cannot name the weights it actually assessed — `MUTABLE_REVISIONS` flags branch names and `latest`. **`decoding_params` belongs in a provenance contract** because for an LLM the weights alone do not determine behaviour: the same model at `temperature: 0.9` and `temperature: 0` produces materially different faithfulness and robustness numbers, so every reproduced metric is conditional on them.

**Validation keys off the mode, not off artefact presence.** `check_model_meta` previously gated every check on `bool(model_artifact_uri)`, which marked them all *not applicable* whenever no artefact was uploaded — so a dossier could declare `model_format: huggingface` with no artefact anywhere and pass intake in silence. The per-mode tables in `aaa/tools/annex_iv_validator/checks/model_meta/rules.py` replace that: `MODE_REQUIRES` for what each mode must declare, `MODE_FORBIDS` for what it must not (a `hosted_api` model has no artefact, so a serialisation format describes nothing), and a format-declared-without-backing check that makes the silent case reachable. Dossiers predating the field are unaffected — an uploaded artefact with no declared mode is treated as `artifact_upload`. `ConditionalFieldStatus.present` accordingly means *the dossier is correct on this point*: value present for a required field, correctly absent for a forbidden one, so one `applicable and not present` reading flags either defect.

**Phase 3 findings are mode-aware.** Absence of weights means different things under different modes, so `aaa/tools/eval_inputs/load/missing.py` records `P3-MODEL-MISSING` only where an upload was promised; the reference modes get `P3-MODEL-BY-REFERENCE` (the model is named by design; what is true is that this pipeline did not recompute metrics from weights) and `not_provided` gets `P3-MODEL-NOT-PROVIDED`. Silence was rejected as an option — it would hide from the report that the metrics were never independently verified.

Separately, `P3-MODEL-TYPE-MISMATCH` (`load/declared_type.py`) compares the declared implementation *library* against the loaded estimator's module path, catching a dossier that names one library while the artefact ships another. The comparison is deliberately restricted to the library: estimator family is not checked, because a declared `tfidf_logistic_regression` legitimately ships as a `sklearn.pipeline.Pipeline` with the `LogisticRegression` in a nested step.

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
| **Agentic system** (tool-using) | L-branch | 1, **L**, 5, 6 | trajectory_audit, prompt_injection_suite | Cyber | Annex IV §1–§5, §7–§9; system prompt; **tool inventory** (names + permitted scopes); `trace_sample_uri` — client-exported trace sample (Langfuse-shaped JSON array of tool-call traces); guardrail config |
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

Every phase artefact passes through the Verifier before the Orchestrator accepts it. The Verifier
reviews the artefact against its **stamped `artefact_uri` + the per-claim `evidence_uris`** the
agent attached (see §3.2a); a populated `artefact_uri` alone satisfies traceability. It returns:

- `accept` — artefact admitted to state
- `accept_with_notes` — admitted; notes appended to compliance matrix
- `rerun` — phase agent re-invoked with the critique as additional context (max 2 reruns)
- `escalate_hitl` — deferred for human review (the pipeline still completes; see §8.4)

Escalation is **reserved for substance**: `escalate_hitl` only when `factual_accuracy = 0` (claims
contradict the evidence) or a confirmed **material** non-conformity. A low `evidence_linkage` /
`output_contract` / `completeness` score alone routes to `rerun`, not HITL. The Phase-6 **report**
artefacts (T17/T18) are exempt — a self-referential escalation on the report (e.g. "PASS_WITH_OBS
despite INSUFFICIENT_EVIDENCE") is downgraded to `accept_with_notes` unless it flags a genuine
factual error. Phase agents retrieve in a bounded **ReAct** loop, seeding their core articles and
optionally emitting a `retrieval_plan` for one extra round of regulatory/client-doc retrieval.
Accumulated hits are de-duplicated on `(source_uri, chunk_index, text)`, re-ranked by descending
score and capped per kind (`evidence_retrieval/dedup.py`, F6). The last round the budget allows is
marked `final_round`; a reply that still carries a `retrieval_plan` is re-prompted once with
retrieval closed and then refused, so a plan cannot be filed as an artefact
(`evidence_retrieval/terminal_round.py`, F15). Phase 6 has no retrieval channel — it composes from
admitted artefacts and runs the same path with `rounds=0`.

Phase 6's `report_signed` is derived by the runtime, never asserted by the model
(`report_architect/signing.py`, F15): a report is signed only when it rendered to a retrievable
URI, carries an executive summary, was synthesised rather than machine-assembled, and is not
pending human review. Failing conditions are recorded on the T18 as `signature_withheld`. A
`DISCLAIMER_OF_OPINION` is signed — under ISAE 3000 a disclaimer is a conclusion reached.

### 8.3 Checkpointing

In graph-fallback mode, `AuditState` is checkpointed to Postgres after every successful stage transition (LangGraph `PostgresSaver`); in ReAct mode the equivalent replay record is the per-turn `react_decision_history` embedded in the final state (loop-level checkpointing is not yet implemented). This allows:
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

#### 8.4a Deferred-HITL workflow (defer → provisional → finalize)

HITL no longer hard-pauses the graph. When any artefact is `escalate_hitl`, the pipeline still runs
through Phase 6 and emits a **provisional** report (T17/T18 carry
`report_status = PROVISIONAL_PENDING_HITL`), so the customer folder is never left inconsistent. The
writer also exports an editable **review packet** `<id>_hitl_review.json`
(`aaa/tools/hitl_review/`): one entry per escalated artefact — or, when `hitl_required` was set by an
adverse verdict rather than a Verifier escalation, one entry per artefact implicated by the material
findings behind it (`escalation_source: "verdict"`, same case schema) — with its phase, issues,
scores, article citations, and the **fetched `evidence_uris`**, plus empty human fields
(`human_decision ∈ {accept, uphold_escalation, override}`, `human_suggested_verdict`,
`human_rationale`, `reviewed_by`). After the human edits the packet,
`python -m scripts.finalize_hitl <id>` applies the decisions (`apply_human_decisions`), recomputes
the compliance matrix + KPIs (`node_compliance_matrix`), and re-renders the **FINAL** T17/T18
(`ReportArchitect._build_t17/_build_t18`). Remaining unresolved cases leave the report
`PARTIALLY_RESOLVED`/provisional — correct when, e.g., a model is genuinely unverifiable.

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

**Implemented.** `aaa/observability/tracing.py::configure_llm_tracing()` registers
Langfuse as a LiteLLM `success_callback`/`failure_callback` — a real trace per
LLM call, with zero SDK calls outside that one seam
(`aaa/platform/flex_retry/flex_acompletion.py`). No-op until both
`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are set (create a project at
`http://localhost:3003` first — see §14.4), so tests/CI are unaffected.
Every call inside a phase-agent dispatch is tagged `metadata={"session_id":
<engagement_id>, "tags": [<agent name>]}` (bound via a context-propagating
`ContextVar`, threaded correctly across `run_coro_blocking`'s worker-thread
hop — see `aaa/observability/trace_context.py` /
`aaa/platform/async_timeout.py`), so every LLM call of one engagement groups
into a single Langfuse session, filterable per agent.

**Cost/latency dashboard**: real, via Prometheus + Grafana (the `obs` compose
profile, §14.4) — `LLM_CALL_COUNTER` / `LLM_COST_COUNTER` /
`LLM_LATENCY_HISTOGRAM` / `LLM_TOKEN_COUNTER` /`PHASE_LATENCY_HISTOGRAM`, all
labelled by agent/model (never by `engagement_id` — an unbounded label would
grow one Prometheus time series per engagement forever; per-engagement detail
lives in the Langfuse session instead).

**Not implemented** (future work): OpenTelemetry spans, and trace-ID linkage
into individual Evidence Store artefacts. The `logs/audit/llm_audit.jsonl`
file (SETUP.md §7–8) remains the canonical, always-on LLM audit trail
independent of whether Langfuse credentials are configured.

### 9.3 Guardrails

**Intake-level guardrails** (before any LLM receives client data):
- **Schema validation first**: `annex_iv_validator` runs JSON-Schema validation against the Annex IV §1–§9 bundle *before* any field is passed to an LLM context. Invalid payloads are rejected at the API layer with a field-level error list; they never enter the agent graph.
- **Intake completeness gate**: `intake_completeness_calculator` must return `intake_completeness_score ≥ 0.80` before the Orchestrator instantiates any phase agent. This is enforced as a precondition in `aaa/agents/tier1/orchestrator/` (`_node_stage_0`); it is not a soft warning.
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
| Orchestration framework | **ReAct loop** (in-repo, `orchestrator/react/`) over **LangGraph** (MIT) fallback | Production sequencing is LLM-decided with code-enforced gates and an auditable decision history; the LangGraph state graph + Postgres checkpointer remain as the deterministic offline/CI fallback. |
| Agent runtime | LangChain (MIT) agents on top of LangGraph nodes | Mature tool-calling, structured-output support |
| Model routing | **LiteLLM** (MIT) | Single OSS wrapper calling Anthropic Claude, OpenAI GPT, DeepSeek, Mistral, local Ollama, etc. — no provider lock-in |
| Vector store | **Qdrant** (Apache-2.0, local Docker) | Regulatory corpus + RAG over past engagements; replaces pgvector — no Postgres extension required |
| Object store | **MinIO** (AGPL-v3, S3-wire-compatible) | Evidence Store; identical API in dev and prod |
| Relational store | **PostgreSQL** | `AuditState` checkpoints, `evidence` index, engagement metadata |
| Queue | **Valkey Streams** (BSD-3, Linux-Foundation Redis fork) | Inter-stage dispatch on parallel branches |
| Front-end | **Streamlit** (implemented demo) + optional future portal | Self-serve intake, uploads, run trigger, and report download in the thesis MVP |
| API | **FastAPI** (MIT) | Health, engagement CRUD, customer file uploads, intake submission, run trigger, report metadata, and PDF retrieval; online governance integration remains via `cgsa_pull` (§10.2) |
| Observability | **Langfuse** (Apache-2.0) — LLM tracing; **Prometheus** + **Grafana** — metrics/dashboards; **Loki** + **Grafana Alloy** — log aggregation (Alloy, not Promtail, which reached EOL 2026-03-02). All four behind the optional `obs` compose profile (§14.4) | LLM traces, cost/latency dashboards, log aggregation |
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

1. **Resolve `assessment_id`** — from `client_submission.cgsa_assessment_id` where an entry point declares one (API, CLI). The wizard does not: S4 mints the id and files the assessment against an organisation and a system, and the organisation it describes never sees it, so asking a customer for it produced a field only this repository could fill. `cgsa_pull.resolve_assessment_id` matches the provider and system names the customer already gave against every assessment's `metadata.organisation_name` / `system_under_audit`, dropping legal forms and version suffixes. No match, or more than one, resolves to `None`: attaching another system's governance history is worse than attaching none.
2. **Pull** — HTTP GET to S4's FastAPI with exponential back-off (5 attempts, 1–32 s). 404 ⇒ HITL escalation ("CGSA assessment not yet available"). 5xx ⇒ retry. 401 ⇒ refresh OpenBao token once, then HITL.
3. **Pin-check** — assert `response.headers["X-Schema-Version"] == "1.0.0"`; on drift ⇒ Verifier `escalate_hitl` with full diff.
4. **`schema_validate`** against the pinned `uagf_cgsa_aaa_schema.json` (vendored in `aaa/schemas/cgsa/v1.0.0/`).
5. **Persist** the raw payload to MinIO under `engagements/{engagement_id}/cgsa/{assessment_id}.json` with SHA-256 in the `evidence` table.
6. **Hydrate** `AuditState` per the §5.4 consumption map (every CGSA-prefixed field set in one transaction).
7. **Cross-check** Phase 1 `risk_tier` vs `metadata.risk_tier`; mismatch ⇒ `cgsa_risk_tier_match = False` and HITL flag (§8.4).
8. **Emit** `cgsa_ingested` span (Langfuse) with `assessment_id`, byte size, validation duration.

**Schema-drift CI gate.** A nightly GitHub Actions job (`s4_contract.yml`) pulls the live `uagf_cgsa_aaa_schema.json` from the S4 repo and runs `jsonschema_diff` against the vendored copy. Any breaking change opens an issue and fails the build until either AAA updates its pinned version or S4 reverts.

**Fixture-backed CGSA (no live S4).** For the Streamlit demo (§14), CLI smoke runs, and unit tests, `cgsa_pull` reads local exports. `CGSA_FIXTURE_DIR` is a **path-separated search order**, not a single directory (default `mock:scripts/fixtures/cgsa`); each root is tried directly and then walked to a bounded depth, so a case's own `mock/<case>/cgsa/` wins over a shared directory. `AAA_CGSA_FIXTURE_DIR` overrides both outright.

**Two dialects, and they are not interchangeable.** `s5-aaa-adapter-v1.0` is the *evaluated* export: `final_maturity_score` and `threshold_score` on every control, and a full-article compliance matrix. `1.0.0` is the *self-assessment* export: scores and prose, no thresholds, a narrower matrix. Only the first can raise a control-level non-conformity, because only it carries a threshold for a control to fall below — so substituting one for the other does not fail, it silently produces a softer audit. `cgsa_pull.compat.payload_profile` names the difference, `resolve_assessment_id` prefers an evaluated export over a self-assessment of the same system, and `run_preflight` (§14.11) refuses a run whose dialect differs from its baseline's.

### 10.3 S6 XAI / S7 Security Providers (`aaa/integrations/`)

The explainability/fairness (Art. 13) and security/robustness (Art. 15)
capabilities are **switchable providers**, each toggled independently via
`.env` (`.env` *is* the config file; environment variables override it):

| Variable | Values | Default |
|---|---|---|
| `S6_XAI_MODE` / `S7_SEC_MODE` | `internal` \| `external` | `internal` |
| `S6_XAI_BASE_URL` / `S7_SEC_BASE_URL` | service root | `http://localhost:8006` / `:8007` |
| `S6_XAI_BEARER_TOKEN` / `S7_SEC_BEARER_TOKEN` | optional bearer token | empty |

- **internal** — adapters package the pipeline's own artefact references
  (T09/T10/T12/T13 for XAI; T11/T13/T15 for security) into a shared evidence
  document shape.
- **external** — **S5** (this codebase) POSTs a versioned hand-off envelope
  (`handoff_schema_version: 1.0.0`, full audit state inside) to
  `{BASE_URL}/api/v1/evaluate` with retry/back-off mirroring `cgsa_pull`
  (immediate fail on 401/404, exponential retry on 5xx/transport errors).

**Scope-derived gating** (`aaa/integrations/gating.py`) — a provider is only
invoked (internal *or* external) when the engagement's scope actually calls
for its evidence, mirroring the compliance-matrix's own treatment of
Art.13/Art.15 as core only at the high risk tier:
- `xai_required` — S6 only for a **high-risk** engagement with an evaluable
  model (`model_artifact_uri` + `task_type` + a dataset URI). A model supplied
  by reference rather than upload (§6.3) carries no `model_artifact_uri`, so
  it does not open this gate.
- `security_required` — S7 for every **high-risk** engagement (Art.15 is
  core there), *or* any **LLM/agentic** system regardless of risk tier (the
  prompt-injection / runtime-detection surface exists without a model file).

Not-required lands `{"evidence_source": "not_required", "reason": "..."}`
without any network call; the PDF and results page render the reason instead
of an empty section.

**Full-state echo, guarded** (`aaa/integrations/postprocess.py`) — the agreed
contract has the partner echo the **entire** audit-state JSON back with only
its own section populated. S5 never trusts the echo beyond that:
`extract_partner_sections` pulls out *only* `xai_evidence` /
`security_evidence` and discards everything else; if the echo also carries a
protected field (`final_verdict`, `blocking_findings`, `compliance_matrix`,
…) that is logged as a clobber attempt and still never applied.

**Verdict-aware merge, downgrade-only** — a partner's section may carry an
`article_verdicts` map (e.g. `{"Art.13": "FAIL"}`). The compliance-matrix
node (`aaa/agents/tier1/phases/compliance_matrix/partner_verdicts.py`) merges
it under a strict downgrade-only rule: a partner verdict only ever applies
when it is *worse* than S5's own current verdict for that article (severity
PASS < PASS_WITH_OBSERVATIONS < INSUFFICIENT_EVIDENCE < FAIL) — a partner
PASS can never promote a verdict S5 has not independently admitted. Each
partner is scoped to its own article by construction (S6 → Art.13 only,
S7 → Art.15 only). Absent `article_verdicts`, the merge is a no-op — today's
report-only behaviour for every existing fixture.

`aaa/integrations/dispatch.py::apply_provider_evidence` runs after Phase 5 in
both pipeline paths (before the gating check, before the compliance-matrix
node) and lands the results in the `AuditState` evidence zones (`xai_evidence`
/ `security_evidence` + `*_source` markers), **fail-soft** — a dead partner
service records an error stub, never breaks the run. The report and the
results UI render these zones source-agnostically; customers never see which
provider produced a section, or whether it was skipped by gating.
`build_handoff` also validates the S6-required stage-B fields and returns
fail-soft warnings when they are missing. Which fields those are depends on
`model_access_mode` (§6.3): under the reference modes S6 resolves the model
from the vendor, so the warnings cover `model_reference.provider` /
`.model_id` / `.revision` — the fields that identify *which* model — rather
than `task_type` / `model_format`, which describe a file that does not exist.
`target_column` (supervised tasks) and `positive_label` (binary
classification) are warned on regardless of mode.

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
| Wang 2024 — *Autonomous-agent role specialisation* | 14-agent role taxonomy (§3); Orchestrator planner-executor pattern (§6) |
| Falco 2021 — *Independent audit principle* | Verifier as independent agent (§3.1); Tier-3 Cyber sub-agent independence (§3.3) |
| Gebru 2021 — *Datasheets for Datasets* | T06 datasheet template (§4A); Phase 2 evidence rubric; Stage B `training_data_description` field (Annex IV §2) |
| **Mitchell 2019 — *Model Cards for Model Reporting*** | T02 system card template (§4A); Stage A triage form structure (provider, intended purpose, deployment context, performance metrics) — Model Cards are the practitioner predecessor of the Annex IV §1 general description requirement. |
| **Arnold 2019 — *FactSheets: Increasing Trust in AI Services through Supplier's Declarations of Conformity*** | Stage A self-declaration pattern; `declared_*` fields in `StageATriage`; the concept of client-declared values verified by an independent auditor maps directly to IBM's FactSheet supplier-declaration model. |
| EU AI Act 2024 — *Art. 9, 11, 43, Annex III, Annex IV* (primary specification) | §3.5 (Art. 43 procedure selection), §3.6 (Annex III taxonomy), §6 Stage 0 (three-stage intake aligned with Art. 11 + Annex IV §1–§9), §6.2 (risk-tier CSP), §5.4 (Art. 9/10/13/14/17 hand-off from S4) |

---

## 13. Summary

The AAA is a **hub-and-spoke orchestrator-worker system of 14 agents** that consumes the S4 `uagf_cgsa_aaa_schema.json` payload via a pull at Phase 5 (§10.2) and emits an EU AI Act-compliant conformity-assessment report at Phase 6 covering **Articles 9, 10, 11, 13, 14, 15, 17, 43, Annex III, Annex IV, and GPAI 51–55**. Engagements begin with a three-stage Annex-IV-aligned intake — Stage A triage (modality / risk / Annex III declaration), Stage B dossier (Annex IV §1–§9 technical documentation), Stage C scoped live-system access — captured as templates T01a/T01b/T01c and validated against published JSON Schemas before Phase 1 runs (§6 Stage 0). Three always-on cross-cutting agents (Orchestrator, Verifier, Regulatory RAG) coordinate six phase agents through the Orchestrator's ReAct loop — LLM-decided sequencing with code-enforced gates and an auditable per-turn decision history (LangGraph state machine retained as offline/CI fallback) — with LLM/agentic systems routed down the UAGF-TAM-L branch and progressive-disclosure spawns of Cyber and Privacy specialists when their evidence is needed (Tier-3 agents justified by Mökander 2023 application-layer audit obligations, §3.3). Twenty MIT-licensed artefact templates (§4A) are the durable currency between agents; the Orchestrator's deterministic Article 43 procedure selector (§3.5) and the published Risk-Tier × Phase CSP catalogue (§6.2) make every routing decision regulator-replayable. Three operational KPIs — `intake_completeness_score`, `completeness_score`, and `regulatory_coverage_pct` (§9.1) — are computed deterministically on every engagement and benchmarked against the supervisor's human audit on the five thesis case studies (finance / retail forecasting / logistics-critical-infrastructure / LLM-agentic / NLP). The Ready-to-Deploy Plan (§14) makes every exposé milestone executable via a single `make` target, from `make m3-linear` (Week 7) through `make deploy-prod` (Week 24).

---

## 14. Ready-to-Deploy Plan

This section is the operational counterpart to §1–§13: every component declared above has a build, a runtime command, and a smoke test. The plan is staged so the exposé Week-by-Week milestones (M1–M9) are each satisfiable by running a single `make` target.

### 14.1 Repository Layout

```
UAGF_TAM_AAA/
├── ARCHITECTURE.md                      # this document
├── pyproject.toml                       # package metadata (hatchling; deps in requirements files)
├── requirements.txt                     # runtime dependencies (pip-managed)
├── requirements-dev.txt                 # dev/test dependencies (-r requirements.txt + lint/test tools)
├── Makefile                             # one-line targets per milestone
├── docker-compose.yml                   # local dev: Postgres, Qdrant, MinIO, Valkey, Langfuse, OpenBao
├── docker-compose.prod.yml              # production overlay
├── .env.example                         # 12-factor env template
├── .github/
│   └── workflows/
│       ├── ci.yml                       # lint + pytest + coverage gate
│       ├── s4_contract.yml              # nightly schema-drift check (§10.2)
│       ├── templates_release.yml        # publishes uagf-tam-templates to PyPI  [planned]
│       └── streamlit_deploy.yml         # demo deployment to Streamlit Cloud  [planned]
├── aaa/                                 # layout convention: module/sub-module/file —
│   │                                    # families live in subpackages (pdf/theme.py,
│   │                                    # step4/matrix.py), never prefix-files (pdf_theme.py)
│   ├── __init__.py
│   ├── __main__.py                      # python -m aaa → launcher front door
│   ├── cli/                             # sub-commands: cmd/run.py, cmd/report.py, parsers
│   ├── settings/                        # pydantic-settings package (sections + model)
│   ├── agents/
│   │   ├── base/                        # BaseAgent, contracts, audit, prompts
│   │   ├── doc_intelligence/            # pre-intake extraction (queries/stage_a|b.py)
│   │   ├── intake_validator/            # Stage 0 validation + completeness gate
│   │   ├── tier1/
│   │   │   ├── orchestrator/            # graph, runner, sequential, wrappers
│   │   │   ├── phases/                  # nodes/{plan,stage0,route,hitl_checkpoint},
│   │   │   │                            # phase_runners/phase/p1..p6, compliance_matrix
│   │   │   ├── regulatory_rag/          # retrieval agent (kb/core.py, kb/extended.py)
│   │   │   └── verifier.py              # independent quality gate
│   │   ├── tier2/                       # Phase 1–6 agents; artefact builders as
│   │   │                                # subpackages (t09/, t14/, t18/, opinion/)
│   │   └── tier3/                       # UAGF-TAM-L, Cyber, Privacy specialists
│   ├── api/                             # FastAPI app, schemas, store, routes/
│   ├── data/                            # file-based persistence + customer deliverables
│   ├── integrations/                    # S6 XAI / S7 Security providers (§10.3):
│   │   ├── handoff.py                   # versioned audit-state hand-off envelope
│   │   ├── xai/ · security/             # internal adapters + external HTTP clients
│   │   └── dispatch.py                  # lands evidence in state after Phase 5
│   ├── launcher/                        # one-command start-up (python -m aaa)
│   ├── observability/                   # logging, metrics, error capture, LLM audit
│   ├── platform/
│   │   ├── prompt_registry/             # prompt runtime (prompt/path.py) from PROMPT.md
│   │   ├── state/                       # audit_state/{parts,evidence,compliance}, cgsa/
│   │   └── evidence/                    # EvidenceStore (MinIO-backed)
│   ├── tools/                           # deterministic audit tools; variants as
│   │   │                                # subpackages (compute/, scan/, explain/, load/)
│   │   └── report_render/               # pdf/{theme,builder,…}.py + text/ fallback
│   └── ui/
│       ├── app.py                       # Streamlit wizard entry point (§14.7)
│       ├── styles/                      # badges, cards, gauge, theme
│       └── wizard/                      # step0–step4 packages (step3/stage_a/, step3/provenance/vendors/, step4/)
├── schemas/
│   └── cgsa/v1.0.0/
│       └── uagf_cgsa_aaa_schema.json    # vendored S4 schema (canonical pinned copy)
├── templates/                           # 20 JSON Schemas (T01a/T01b/T01c + T02–T18)
├── packages/
│   └── uagf_tam_templates/              # MIT-licenced distributable template package
│       ├── pyproject.toml
│       ├── src/uagf_tam_templates/      # load_schema / validate / render_partial API
│       └── tests/
├── scripts/                            # same module/sub-module/file convention as aaa/
│   ├── setup/                          # bootstrap: steps/{env,infra}.py, cli, shell
│   ├── ingest_regulatory_corpus/       # corpus build: checker/, iso/, pdf/ subpackages
│   ├── fixtures/
│   │   ├── uci_german_credit/           # stage_a.json / stage_b.json / stage_c.json
│   │   └── cgsa/                        # uci-german-credit-001.json + smoke fixtures
│   └── smoke_group{6,7,8,9,11}.py       # ad-hoc end-to-end smoke tests
├── tests/                               # pytest test suite
│   ├── unit/                            # per-agent + per-tool
│   ├── contract/                        # CGSA pull + schema drift
│   ├── golden/                          # frozen end-to-end traces
│   └── e2e/                             # German Credit, M5, Hamburg, LLM cases
├── infra/
│   ├── tofu/                            # OpenTofu modules (Hetzner / Scaleway)
│   └── runbook.md                       # ops playbook (§14.9)
├── data/
│   ├── Updated_Expose_S5_UAGF_TAM_AAA_Updated.txt  # exposé document
│   └── files/                           # schema explorer JSX + supplementary files
└── out/                                 # generated audit outputs (gitignored in production)
```

> **Note:** This section mixes the implemented thesis MVP with the broader target deployment.
> Where a future-state component is mentioned (for example, a hardened production portal or
> full cloud deployment pipeline), it should be read as an architectural extension rather than
> a claim that the current repository already ships that production surface.

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
langfuse>=4.14.2,<5
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
OPENAI_API_KEY=                          # required for gpt-5.6-sol / gpt-5.6-terra / gpt-5.6-luna
ANTHROPIC_API_KEY=                       # optional fallback (Claude family via LiteLLM)
DEEPSEEK_API_KEY=                        # cost-saver fallback
# Model choice is NOT env-configurable. Per-agent assignment lives in
# aaa/platform/model_registry/ (Sol / Terra / Luna roles), with PROVIDER
# switching between the OpenAI and NVIDIA NIM rosters. The former
# LITELLM_MODEL_TIER1/2/3 variables were read by nothing and were removed in
# T-20260806-010; setting them has no effect.
PROVIDER=openai                          # openai | nvidia
LITELLM_FALLBACKS="gpt-5.6-sol>gpt-5.6-terra>gpt-5.6-luna"

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

# --- one-command launcher (python -m aaa) ---
AAA_LAUNCH_DOCKER=auto                    # auto | true | false — start Docker infra
AAA_LAUNCH_MIGRATE=auto                   # run Alembic migrations on start
AAA_LAUNCH_API=true                       # start the FastAPI backend
AAA_LAUNCH_UI=true                        # start the Streamlit UI

# --- CGSA fixture source (demo / CI without a live S4 service) ---
CGSA_FIXTURE_DIR=mock:scripts/fixtures/cgsa  # search order, most specific first
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
    image: quay.io/minio/minio:RELEASE.2025-01-20T14-49-07Z
    command: server /data --console-address ":9001"
    environment: { MINIO_ROOT_USER: aaa, MINIO_ROOT_PASSWORD: aaa-secret }
    ports: ["9000:9000","9001:9001"]
    volumes: ["miniodata:/data"]
    healthcheck: { test: ["CMD","curl","-f","http://localhost:9000/minio/health/live"], interval: 5s }

  valkey:
    image: valkey/valkey:8
    ports: ["6379:6379"]

  # Langfuse v3+ is split into web + worker and requires ClickHouse (analytics),
  # Redis/Valkey (queue) and S3/MinIO (event blobs). The OTEL ingest endpoint
  # the LiteLLM `langfuse_otel` callback posts to exists only from v3.
  clickhouse:
    image: clickhouse/clickhouse-server:25.12
    volumes: [clickhouse_data:/var/lib/clickhouse]

  # Creates the S3 bucket both halves hand events through. Neither MinIO nor
  # Langfuse creates it, and without it the web tier accepts traces that the
  # worker can never consume.
  minio-init:
    image: quay.io/minio/mc:RELEASE.2024-11-05T11-29-45Z
    depends_on: [minio]
    entrypoint: mc mb --ignore-existing local/langfuse

  langfuse-worker:
    image: langfuse/langfuse-worker:4
    depends_on: [postgres, clickhouse, minio, minio-init, valkey]
    environment: &langfuse_env
      # Its own database — Langfuse applies Prisma migrations and Alembic owns
      # the app schema; sharing one database ran both against it.
      DATABASE_URL: postgresql://aaa:aaa@postgres:5432/langfuse
      SALT: dev-only-do-not-reuse
      ENCRYPTION_KEY: <64 hex chars — openssl rand -hex 32>
      CLICKHOUSE_URL: http://clickhouse:8123
      CLICKHOUSE_MIGRATION_URL: clickhouse://clickhouse:9000
      REDIS_HOST: valkey
      LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT: http://minio:9000

  langfuse:
    image: langfuse/langfuse:4
    depends_on: [langfuse-worker, postgres, clickhouse]
    environment: *langfuse_env
    ports: ["3003:3000"]

  openbao:
    image: openbao/openbao:2
    cap_add: [IPC_LOCK]
    environment:
      BAO_DEV_ROOT_TOKEN_ID: dev-root
      BAO_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    ports: ["8200:8200"]

volumes: { pgdata: {}, qdrantdata: {}, miniodata: {} }
```

Bootstrap sequence — one command brings up infra, migrations, API and UI:

```bash
python3.12 -m scripts.setup                         # venv + deps + .env + (optional) docker/migrations
source .venv/bin/activate                           # activate Python venv
make start                                           # python -m aaa: infra + migrate + API + UI (driven by .env)
```

For a manual/component-by-component bootstrap instead of the launcher:

```bash
cp .env.example .env && $EDITOR .env                # add API keys
docker compose up -d                                # Postgres, Qdrant, MinIO, Valkey, Langfuse, OpenBao
python -m alembic upgrade head                      # apply schema migrations
python -m pytest tests/unit                         # gate: must pass before first audit
```

**Optional observability profile.** Prometheus, Grafana, Loki, and Grafana
Alloy are never started by `docker compose up` — they live under a separate
`obs` profile so the default footprint stays six services:

```bash
make obs                             # docker compose --profile obs up -d
# or: docker compose --profile obs up -d
```

- **Grafana** — `http://localhost:3002` (anonymous Viewer for local dev;
  admin/`$GF_SECURITY_ADMIN_PASSWORD`, default `admin`). Auto-provisioned with
  a Prometheus + Loki datasource and a starter "AAA — Audit Pipeline Overview"
  dashboard: LLM calls/cost/latency/tokens by agent, phase latency by phase,
  engagements by final verdict, errors by component, and a Loki panel over
  every `logs/**/*.jsonl` file (including `llm_audit.jsonl` — Loki backfills
  and retains full history, so "past runs" are queryable there too, not just
  in the raw file).
- **Prometheus** — `127.0.0.1:9090` only (not exposed beyond localhost);
  scrapes the FastAPI `/metrics` endpoint on the host via
  `host.docker.internal`.
- **Loki** / **Alloy** — internal-only, no host port; reached only through
  Grafana's datasource proxy.

Configs live under `infra/observability/`. `make obs-down` stops just the
four observability containers, leaving the core stack running.

### 14.5 Makefile — One Target per Milestone

The exposé milestones (M1–M9) map one-to-one onto `make` targets. Each target produces a verifiable artefact.

```makefile
PYTHON := .venv/bin/python
PIP    := .venv/bin/pip
FIXTURE_INTAKE_DIR := scripts/fixtures/uci_german_credit
FIXTURE_CGSA_DIR := scripts/fixtures/cgsa
FIXTURE_RUN := CGSA_FIXTURE_DIR=$(FIXTURE_CGSA_DIR) $(PYTHON) -m aaa.cli run \
    --intake-dir $(FIXTURE_INTAKE_DIR) --cgsa-fixture-dir $(FIXTURE_CGSA_DIR)

# One command to run everything (infra + API + UI), driven by .env:
start: ; $(PYTHON) -m aaa

venv:
	python3.12 -m venv .venv

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

# --- intake targets (fixture bundle) ---
intake-validate:; $(FIXTURE_RUN) --engagement-id eng-validate-001
intake-demo:    ; $(FIXTURE_RUN) --engagement-id eng-demo-001

# --- exposé milestones ---
m3-linear:    ; $(FIXTURE_RUN) --engagement-id eng-m3-001
m4-full:      ; $(FIXTURE_RUN) --engagement-id eng-m4-001
m5-case1:     ; $(FIXTURE_RUN) --engagement-id eng-m5-case1
m5-case2:     ; $(FIXTURE_RUN) --engagement-id eng-m5-case2
m6-case3:     ; $(FIXTURE_RUN) --engagement-id eng-m6-case3
m6-case4:     ; $(FIXTURE_RUN) --engagement-id eng-m6-case4

# --- demo + deploy ---
report-german:; $(FIXTURE_RUN) --engagement-id eng-uci-german-credit-001 --output-file out/eng-uci-german-credit-001.json
demo:         ; .venv/bin/streamlit run aaa/ui/app.py
deploy-staging:; tofu -chdir=infra/tofu workspace select staging && tofu -chdir=infra/tofu apply -auto-approve
deploy-prod:  ; tofu -chdir=infra/tofu workspace select prod    && tofu -chdir=infra/tofu apply
```

### 14.6 CI/CD (GitHub Actions)

Four workflows, each in `.github/workflows/`.

| Workflow | Trigger | Purpose | Failure policy |
|---|---|---|---|
| `ci.yml` | push, PR | four jobs: **lint** (`ruff check .` over the whole repo incl. notebooks, `pylint aaa scripts` at 10/10, `pyright aaa scripts` at zero errors), **security** (bandit SAST + `pip-audit` on the installed environment, both informational), **test** (pytest excluding e2e/golden/contract markers, coverage ≥ 70%, postgres/qdrant/minio services), **smoke** (Streamlit app import-check + `python -m aaa report --all` against the tracked `tests/fixtures/customer_finclear/` deliverables — no LLM, no infra) | lint + test + smoke block merge; security informational |
| `s4_contract.yml` | cron `0 2 * * *` + manual | Pull S4 schema, run `jsonschema_diff` vs `schemas/cgsa/v1.0.0/`, open issue on drift | Open issue, do not auto-merge schema bump |
| `templates_release.yml` | tag `tpl-v*` | Build + publish `uagf-tam-templates` to PyPI under MIT licence | Skip if version exists |
| `streamlit_deploy.yml` | push to `main` (paths: `aaa/ui/**`) | Readiness import-check + Streamlit Cloud redeploy webhook | Notify on failure |

Design decisions baked into `ci.yml`:

- **No `ruff format --check`** — the repo's style gates are ruff-lint + pylint +
  the 50-executable-line cap; a wholesale reformat would wrap long lines and
  break that cap.
- **`pyright aaa scripts` is a hard gate** over the whole production surface —
  the legacy typing debt (46 errors) was cleared on 2026-07-09 and `scripts/`
  folded into the gate once it reached zero errors; new code is additionally
  pyright-gated per file via `check_code.py`.
- **`pip-audit` audits the installed environment** (not `-r requirements.txt`,
  which hard-fails on requirement resolution) and ignores the one advisory
  without a fixed release (`PYSEC-2026-597`, nltk).
- **The smoke job is deterministic**: it renders the customer PDF from
  committed fixtures instead of running the LLM pipeline.

### 14.7 Streamlit Wizard (`aaa/ui/app.py`)

The Streamlit surface is the primary thesis UI. It runs the same intake →
orchestrator → report path as the CLI/API and works without a live S4 service,
resolving CGSA assessments from the roots `CGSA_FIXTURE_DIR` names (§10.2).

It is **two surfaces in one session**. The customer sees a five-step wizard
driven by `st.session_state["step"]`; everything addressed to an auditor lives
in a separate console at `st.session_state["view"] == "admin"`, reached from a
button on the results page. Nothing on a customer surface names a T-number, a
phase id or an artefact URI.

0. **Get started** — company name and system name. The engagement id is
   *derived* (`new_engagement_id` → `eng-<slug>-<hex6>`) rather than asked for:
   it is the auditor's filing reference and means nothing to the person starting
   an audit. Both names flow into `st.session_state["intake_identity"]` and
   outrank extraction when step 3 initialises.
1. **Your documents** — three upload zones (technical documentation, model
   artefact, datasets). Files are stored via `EvidenceStore.store_file(...)`, and
   `ingest_documents()` indexes them into this engagement's collection. That
   ingest is the **only** route free-form technical documentation takes into
   retrieval: `IntakeValidator` indexes just the named Stage B URI fields.
2. **A few questions** — `QUESTION_COUNT` (9) prompts in one `st.form`, covering
   the Stage A fields no document states reliably. Question 4a ("does your
   system also rank, score, match or classify?") is what lets a *composite*
   system be declared: the phase plan is solved from the declaration before any
   phase dispatches, and a purely generative declaration skips model validation
   and output fairness (§6.2).
3. **Check the details** — the Annex IV dossier, and the whole job now that no
   LLM pre-fills it. A `CompletenessReport`-driven checklist ranks the remaining
   gaps by what they are worth against the 0.80 gate, above three tabs ("Your
   system", "The dossier", "Documents, model & data" — 12 upload slots). The
   client's prior CGSA is **looked up**, not asked for (§10.2), and the page
   states in plain words what was found. The run button is deliberately never
   disabled: a disabled primary button tells a customer they may not proceed
   without saying why. Clicking it either starts the audit or lists exactly what
   is in the way.
4. **Your results** — a dashboard, not a report dump: the verdict as a sentence,
   four KPI tiles, the two PDFs that are the customer's to keep, a
   plain-language article breakdown (`client_brief.constants.article_title`) and
   a remediation list ordered by how much each item moves conformity.

**Admin console** (`aaa/ui/admin/`) holds the HITL review packet, T17/T18, the
raw `AuditState`, run integrity and evidence status — the material that was
previously handed to customers who had no use for it.

Step 3 also collects the **model metadata** the evaluation loader and the S6
hand-off require: `task_type`, `model_format` (pre-filled from the uploaded
artefact's filename), `model_framework`, plus `target_column` / `positive_label`
/ `sensitive_feature_columns` (column-aware select boxes once a CSV is
uploaded). Those three resolve through `explicit_data_dictionary`, which reads
the nested `data_dictionary` block *or* the top-level keys: a CLI intake bundle
nests them and the wizard also writes them flat, and reading only one shape
sent Phase 2 a null target column for a dossier that declared one.

For generative systems it then renders the **model-provenance block**
(`aaa/ui/wizard/step3/provenance/`, §6.3), gated on `declared_modality ∈ {llm,
agentic, gpai}` so a tabular customer — who uploads a model file and is done —
never sees it. The block asks the access mode first, and only opens the vendor
branch for the modes where the model is named rather than uploaded. Six
questions are common to every vendor (access mode, task, provider, model id,
version pin, licence and gating); the rest are vendor-specific, because what
constitutes an immutable pin differs — a commit SHA on HuggingFace, a dated
snapshot on OpenAI, a deployment plus api-version on Azure, a pinned model
version on Vertex/AI Studio for Gemini, a container image digest for NIM, a
model ARN on Bedrock. Every answer is stored into a `ModelReference` key
regardless of vendor, so the schema stays uniform and S6 parses one shape no
matter who the customer buys from; `questions_for()` falls back to a generic set
for a provider without a tailored branch, so a vocabulary entry can never render
a blank form. Aggregators get one question the first-party APIs do not:
OpenRouter addresses a *route*, and a single slug can be served by several
upstream providers at different quantizations, so `upstream_provider` records
which weights actually answered — an answer of "routing is automatic" is itself
an audit finding, since it means the weights vary per request.

**No AI pre-fill.** `DocIntelligenceAgent` did two jobs: indexing the uploads,
and spending an LLM call reading Stage A/B values out of them to pre-populate
step 3. Only the first is load-bearing, so the wizard now calls
`ingest_documents()` and not the agent. The agent and
`POST /api/v1/engagements/{id}/extract-triage` are unchanged for callers that
still want pre-fill.

**Styling** is a first-party design system (`aaa/ui/styles/`), not a CDN
framework: two tones — a deep navy `--ink` and an indigo `--brand` — with every
neutral mixed from the ink seed. Verdict hues are the deliberate exception,
since a compliance state must never be carried by colour alone (WCAG 1.4.1).

**Driving it headlessly.** `scripts/wizard_fill` fills the form with Playwright
for a named case bundle, importing every label from the module that renders it
so a rename breaks the driver instead of silently leaving a field blank
(§14.11).

The wizard does **not** embed Langfuse trace replay or an inline PDF viewer;
those remain future UX extensions.

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
| API unhealthy | `/healthz` fails | Inspect `logs/app/app.log` and `logs/api/api.log`; restart `uvicorn aaa.api.main:app --reload --port 8000` | Open runtime bug if reproducible |
| Audit run failed | `POST /run` fails or no result written | Inspect `logs/errors/*.jsonl`, `logs/audit/llm_audit.jsonl`, and `data/results/<id>/` | Escalate to maintainer if repeated |
| Persisted result missing | `/api/v1/data/...` returns 404 after completion | Inspect `data/index.json` and per-engagement directories | Open bug on `aaa/data/` or API routes |
| LLM audit anomaly | unexpected cost/token spike | Aggregate `logs/audit/llm_audit.jsonl` (one JSON record per call: tokens, latency, cost) | Notify prompt/model owner |
| Schema version mismatch | `/api/v1/schema-version` unexpected | Reconcile `CGSA_SCHEMA_VERSION`, vendored schema, and settings | Coordinate schema update before new runs |
| PDF not available | `/report.pdf` returns 404 | Use JSON report and inspect rendering logs | Escalate only if PDF is required |

### 14.10 Smoke-Test Procedure (10-Minute Acceptance)

Run after doc-sensitive or runtime-sensitive changes. The currently implemented
acceptance path is:

1. `python3.12 -m scripts.setup --no-docker --no-migrate` completes successfully.
2. `python -m pytest tests/unit -q` passes.
3. `make start` (or `python -m aaa`) brings up the API + UI; alternatively `aaa api` starts the backend alone.
4. `curl -fsS http://localhost:8000/healthz` returns `status=ok` and the pinned schema version.
5. `curl -fsS http://localhost:8000/metrics > /dev/null` succeeds.
6. `make intake-demo` completes with a JSON summary.
7. `GET /api/v1/data/engagements` returns at least the created demo engagement after a persisted run.
8. The Streamlit 5-step flow is reachable at `http://localhost:8501` (via `make start` or `aaa ui`).

### 14.11 Run Reproducibility (`aaa/tools/run_preflight`, `scripts/wizard_fill`)

Two tools exist because a run that cannot be compared with its baseline is worse
than no run: its differences read as findings.

**`python -m aaa.tools.run_preflight <case-doc> --intake-dir <bundle>`** checks a
planned run against the baseline a case's per-call assessment document pins, and
exits non-zero when it would not be comparable. Four checks: the model and
provider pin resolved from the current environment; the **CGSA dialect** the run
would pull against the one the baseline used; the Stage A declaration; and which
Stage B document slots are filled. It makes no LLM calls.

Resolving *which* run is the baseline is itself a trap the tool closes. The case
document's header names the run that was **assessed**, which is the pre-fix one;
comparing against it measures the fix series rather than the new run. The
controlled post-fix comparison is marked only in
`data/customer/<company>/runs/INDEX.md`, because `run.json` stamps the same
dirty revision on every run in a series. And it is never the flat
`<engagement>_audit_state.json`, which is whichever run under that engagement id
finished last — case 06's archive holds eight, spanning 46.7 % to 100 %
regulatory coverage.

**`python -m scripts.wizard_fill --run`** drives the wizard with Playwright from
a case bundle, so a UI run submits the same payload the CLI does. Every label is
imported from the module that renders it (`_TEXT_FIELDS` from the Stage B spec,
`DOC_UPLOAD_FIELDS` from the wizard constants, `_MULTISELECTS` from the FLI
spec) rather than copied, so a renamed field raises an `ImportError` before a
browser launches instead of silently leaving that field blank. It is headed by
default — a headless run has no window to watch and nothing to interrupt — runs
the preflight before dispatching, and holds the browser open afterwards so the
dashboard stays usable.

### 14.12 Exposé Milestone ↔ Deployment Checklist

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


### 14.13 Thesis-Scope Addendum — Deferred Components & Auxiliary Assets

The architecture above describes the **target system**. For the thesis
deliverables (M1–M9) several components are intentionally deferred, replaced
with lightweight stand-ins, or kept as reference material only. This section
records what is in-scope vs out-of-scope so reviewers do not mistake an
intentional simplification for a gap.

#### 14.12.1 Next.js client portal — deferred

Sections §14.5 and §14.7 reference a **production Next.js portal** as the
user-facing application (multi-tenant SSO, secure Stage C vault form,
embedded PDF.js viewer). For the thesis deliverable D1 the **Streamlit demo
in `aaa/ui/app.py` is the sole UI**:

- All Stage A/B/C flows that would live in the Next.js portal are simulated
  by the Streamlit pages (Stage C is a read-only summary, not a credential
  intake form).
- There is no `frontend/` or `portal/` directory in the repository; the
  ARCHITECTURE references to the Next.js portal describe the *target*
  topology only.
- The `NEXTAUTH_SECRET` / `NEXTAUTH_URL` entries in `.env.example` are
  placeholders kept for documentation parity with §14.8 and have no
  runtime effect on the Streamlit demo.

#### 14.12.2 Storage backends — hybrid current implementation

The current thesis/demo implementation uses a **hybrid storage model**:

- `aaa/api/store.py` keeps live FastAPI engagement state in memory for the
  current process.
- `aaa/data/` persists user-entered engagement metadata, intake payloads,
  uploaded-file metadata, and final audit results to JSON under `data/` (or
  `AAA_DATA_DIR`).
- `aaa/platform/evidence/` provides an `EvidenceStore` over a swappable backend
  (`EVIDENCE_BACKEND`): `memory` is process-local and used by tests and the
  offline smoke; `minio` persists artefacts so a later process — notably
  `python -m aaa report` — still resolves the `minio://` URIs the pipeline
  wrote. A configured-but-unreachable MinIO raises rather than degrading to
  memory, so evidence is never silently lost.

The broader local stack (`docker-compose.yml` + `alembic upgrade head`) still
exists for the future/optional production-style path with Postgres and other
services, but the repo's implemented persistence guarantee today is the local
file-based store in `aaa/data/`.

#### 14.12.3 Schema explorer (`data/files/uagf_schema_explorer.jsx`)

The JSX file under `data/files/` is a **standalone reference document** that
visualises the CGSA schema (`schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json`)
for human reviewers. It is not wired into any runtime:

- It is not imported by the Streamlit demo (`aaa/ui/app.py`).
- The repository does not ship a `package.json` or JSX build pipeline; the
  file cannot be opened or served as-is from this repo.
- It is kept consistent with the schema content (same enums, same required
  fields) and is used as a documentation aid when discussing the schema
  with S4 maintainers and the thesis committee.

If the Next.js portal (14.12.1) is ever built, the explorer can be hosted
inside it; until then, treat it as a static reference artefact.

#### 14.12.4 Components that are *planned* and *required for production* but not for the thesis demo

The following are declared in `ARCHITECTURE.md` and **must exist before
production deployment (M9)** but are not on the critical path for the
thesis demo (M3/M4):

- A production Next.js portal (14.12.1).
- A Postgres-backed engagement repository replacing the current in-memory API store.
- A first-party purge/deletion command for persisted engagements.
- Broader automated coverage beyond the current unit/contract/golden set.

The thesis demo (`make demo`) and the fixture pipeline (`make m4-full`) run
without any of these — they exercise the LangGraph orchestrator, the 13
agents, the CGSA ingest path, and the T01–T18 templates against the bundled
UCI German Credit fixture.
