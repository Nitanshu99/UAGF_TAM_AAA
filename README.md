# AAA — Autonomous AI Auditor

An end-to-end **13-agent pipeline** for EU AI Act conformity assessment. Upload your AI system's documents, answer 8 guided questions, and receive a structured compliance audit with a final verdict, KPI scores, and a downloadable report.

> **Python 3.12 is required.**

---

## Documentation

| File | What it covers |
|------|----------------|
| [USER_MANUAL.md](./USER_MANUAL.md) | **Start here.** Step-by-step setup, offline and online run modes, wizard walkthrough, troubleshooting, quick-reference tables. Written for a complete beginner. |
| [SETUP.md](./SETUP.md) | Technical quick-start — one-command setup, fastest run paths, environment variables. |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Full system design — 13-agent roster, data contracts, LangGraph state machine, artefact templates (T01a–T18), deployment notes. |
| [PROMPT.md](./PROMPT.md) | Canonical LLM prompt specification loaded at runtime by `aaa/platform/prompt_registry.py`. |
| [infra/runbook.md](./infra/runbook.md) | On-call playbook — incident response, service restart, data purge, schema drift procedures. |

---

## How it works

1. **You upload** your AI system's technical documents (model card, data sheet, risk assessment, etc.) and answer 8 short questions.
2. **DocIntelligenceAgent** (agent #13) reads your documents and pre-fills the EU AI Act compliance form — Stage A triage and Stage B Annex IV dossier.
3. **You review** the pre-filled form, edit any field, and confirm when intake completeness reaches ≥ 80%.
4. **13 AI agents** run across 6 audit phases — scope verification, data governance, model validation, fairness testing, governance review, and report generation.
5. **You receive** a final verdict (`PASS` / `PASS WITH OBSERVATIONS` / `FAIL`), a compliance matrix mapped to EU AI Act articles, and a downloadable audit report (PDF + JSON).

---

## Quick start

### 1. Install (one command)

```bash
python3.12 scripts/setup.py --no-docker --no-migrate
```

### 2. Activate the virtual environment

```bash
source .venv/bin/activate        # Mac / Linux
.venv\Scripts\activate           # Windows
```

### 3. Run the wizard (offline — no API key needed)

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

Open `http://localhost:8501` in your browser. Stop with `Ctrl + C`.

For the full setup guide including online mode, see [USER_MANUAL.md](./USER_MANUAL.md).

---

## Agents

| # | Agent | Model | Role |
|---|-------|-------|------|
| 1 | Orchestrator | gpt-5.5 | Plans the audit, sequences phases, routes LLM/agentic systems |
| 2 | Verifier | gpt-5.5 Flex | Independent critic — gates every phase artefact before it enters the compliance matrix |
| 3 | Regulatory RAG | gpt-5.4-nano | Answers "what does Article X require?" from the 1 200-chunk corpus |
| 4 | Scope Agent (P1) | gpt-5.4 | Verifies declared modality, risk tier, Annex III sections |
| 5 | Data Auditor (P2) | gpt-5.4 | Data quality, governance, special-category data scan |
| 6 | Model Validator (P3) | gpt-5.5 Flex | Performance metrics, explainability, robustness |
| 7 | Output Fairness Tester (P4) | gpt-5.4-mini | Demographic parity, disparate impact, subgroup analysis |
| 8 | Governance Agent (P5) | gpt-5.5 Flex | Ingests S4 CGSA findings, maps to compliance matrix |
| 9 | Report Architect (P6) | gpt-5.4 Flex | Assembles T17 compliance matrix and T18 audit report |
| 10 | UAGF-TAM-L | gpt-5.5 Flex | LLM/agentic branch — RAGAS, prompt injection, trajectory audit |
| 11 | Cybersecurity Agent | gpt-5.4 | Adversarial robustness, Art. 15 evidence |
| 12 | Privacy / DPO Agent | gpt-5.4 | GDPR Art. 9 lawful-basis, DPIA cross-reference |
| 13 | DocIntelligenceAgent | gpt-5.4 | Pre-intake — reads uploaded documents and auto-fills the compliance form |

---

## Entry points

| Surface | Command | Purpose |
|---------|---------|---------|
| Streamlit wizard | `streamlit run aaa/ui/app.py` | 5-step guided UI with document upload and auto-fill |
| CLI | `python -m aaa.cli run --intake-dir scripts/fixtures/uci_german_credit --offline` | Fixture-based offline run |
| FastAPI | `uvicorn aaa.api.main:app --reload --port 8000` | REST API — Swagger at `http://localhost:8000/docs` |

---

## REST API

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/engagements` | Create engagement |
| `POST` | `/api/v1/engagements/{id}/files` | Upload a customer file |
| `POST` | `/api/v1/engagements/{id}/extract-triage` | Run DocIntelligenceAgent over uploaded files |
| `POST` | `/api/v1/engagements/{id}/intake` | Submit Stage A / B / C payloads |
| `POST` | `/api/v1/engagements/{id}/run` | Run full audit pipeline |
| `GET` | `/api/v1/engagements/{id}/report` | Verdict, KPIs, report URIs |
| `GET` | `/api/v1/engagements/{id}/report.pdf` | Rendered PDF report |

---

## Regulatory corpus

1 200 chunks indexed in Qdrant across five sources:

| Source | Chunks |
|--------|--------|
| EU AI Act (2024/1689) | 339 |
| GDPR | 288 |
| ISO/IEC 42001:2023 | 88 |
| ISAE 3000 (Revised) | 411 |
| ISO 19011:2018 | 74 |

Run once to populate: `python3.12 scripts/ingest_regulatory_corpus.py` (requires Docker + OpenAI key). See [USER_MANUAL.md § Part 6](./USER_MANUAL.md) for step-by-step instructions.

---

## Repository layout

```
UAGF_TAM_AAA/
├── README.md                        ← you are here
├── USER_MANUAL.md                   ← start here for setup and usage
├── SETUP.md                         ← technical quick-start
├── ARCHITECTURE.md                  ← full system design
├── PROMPT.md                        ← canonical agent prompts (runtime dependency)
├── aaa/
│   ├── agents/
│   │   ├── doc_intelligence.py      ← agent #13: pre-intake document extraction
│   │   ├── intake_validator.py      ← Stage 0 validation + T01c
│   │   ├── tier1/                   ← Orchestrator, Verifier, RegulatoryRAG
│   │   ├── tier2/                   ← Phase 1–6 agents
│   │   └── tier3/                   ← UAGF-TAM-L, Cyber, Privacy
│   ├── api/main.py                  ← FastAPI endpoints
│   ├── cli.py                       ← python -m aaa.cli run ...
│   ├── platform/
│   │   ├── evidence.py              ← EvidenceStore (MinIO-compatible)
│   │   ├── model_registry.py        ← per-agent model + tier assignments
│   │   ├── prompt_registry.py       ← loads prompts from PROMPT.md at runtime
│   │   └── state.py                 ← AuditState, DocExtractionResult, all TypedDicts
│   ├── tools/                       ← 40+ deterministic audit tools
│   └── ui/app.py                    ← Streamlit 5-step wizard
├── data/
│   ├── eu_ai_act_compliance_checker.json   ← FLI questionnaire (scope gate)
│   └── regulatory_corpus/           ← source PDFs / HTML for Qdrant ingestion
├── scripts/
│   ├── setup.py                     ← one-shot environment bootstrap
│   ├── ingest_regulatory_corpus.py  ← loads 1 200 chunks into Qdrant
│   └── fixtures/                    ← sample intake data for offline testing
├── templates/                       ← T01a–T18 JSON Schema + Jinja2 templates
├── infra/
│   └── runbook.md                   ← on-call incident playbook
└── tests/                           ← unit / contract / golden / e2e
```
