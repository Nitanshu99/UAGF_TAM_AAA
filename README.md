# AAA — Autonomous AI Auditor (S5 Thesis)

AAA is an end-to-end **12-agent audit pipeline** for AI-system conformity assessment. It validates Stage A/B/C intake evidence, runs specialised audit agents, consolidates findings into a compliance matrix, and produces a customer-facing **T18 audit report** in **JSON and PDF**.

The current implementation includes:

- prompt runtime loaded from [`PROMPT.md`](./PROMPT.md) via `aaa/platform/prompt_registry.py`
- per-engagement client-document RAG (`client_docs_{engagement_id}`) with `text-embedding-3-large`
- materiality-aware findings and remediation ownership / priority fields
- management-response shells, formal auditor opinion, risk heat-map, and maturity radar
- minimal customer workflow across **CLI**, **FastAPI**, and **Streamlit**

> **Python 3.12 is required.**

## Documentation Map

| File | Purpose |
|------|---------|
| [`README.md`](./README.md) | High-level project overview and quick start. |
| [`SETUP.md`](./SETUP.md) | Plain-English installation and first-run guide. |
| [`USER_MANUAL.md`](./USER_MANUAL.md) | Developer/operator guide for CLI, API, UI, tests, and troubleshooting. |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Full multi-agent architecture, data contracts, and deployment notes. |
| [`PROMPT.md`](./PROMPT.md) | Canonical prompt specification for the LLM agents. |
| [`UPDATE.md`](./UPDATE.md) | Implemented task backlog and acceptance criteria history. |

---

## What Ships Today

### Implemented workflow

1. **Customer provides evidence**
   - Stage A triage
   - Stage B Annex IV dossier
   - optional Stage C scoped access
   - optional file uploads for risk docs, post-market docs, LLM artefacts, datasets, and model files
2. **`IntakeValidator`** validates T01a/T01b, computes `intake_completeness_score`, writes T01c, and ingests uploaded client docs into per-engagement Qdrant collections when available.
3. **`Orchestrator`** runs Phase 1–6 and the specialist branches.
4. **Specialist agents** generate T02–T16 artefacts.
5. **`ReportArchitect`** generates:
   - `T17_compliance_matrix`
   - `T18_audit_report`
   - `auditor_opinion`
   - `management_response`
   - `risk_heatmap_uri`
   - `maturity_radar_uri`
   - rendered PDF/JSON report artefacts
6. The customer receives:
   - final verdict
   - KPI summary
   - T17 JSON
   - T18 JSON
   - PDF report when available

### Main entry points

| Surface | Purpose | File |
|---------|---------|------|
| CLI | Offline/fixture-driven full engagement run | `aaa/cli.py` |
| FastAPI | Engagement creation, file upload, intake submission, run, report retrieval | `aaa/api/main.py` |
| Streamlit | Demo UI with uploads and report downloads | `aaa/ui/app.py` |

---

## Repository Layout

```text
UAGF_TAM_AAA/
├── ARCHITECTURE.md
├── README.md
├── SETUP.md
├── USER_MANUAL.md
├── PROMPT.md
├── UPDATE.md
├── aaa/
│   ├── agents/                      # IntakeValidator + tier1/tier2/tier3 agents
│   ├── api/main.py                 # FastAPI upload-to-report workflow
│   ├── cli.py                      # `python -m aaa.cli run ...`
│   ├── platform/
│   │   ├── evidence.py             # EvidenceStore + binary-safe store_file()
│   │   ├── prompt_registry.py      # Prompt runtime sourced from PROMPT.md
│   │   └── state.py                # AuditState / findings / remediation types
│   ├── tools/
│   │   ├── client_doc_ingest.py    # per-engagement client-document RAG
│   │   ├── regulatory_coverage.py
│   │   ├── report_render.py
│   │   ├── risk_heatmap_render.py
│   │   └── maturity_radar_render.py
│   └── ui/app.py                   # Streamlit intake + uploads + downloads
├── scripts/
│   ├── setup.py
│   ├── ingest_regulatory_corpus.py
│   └── fixtures/
├── templates/                      # T01a–T18 schema files
└── tests/                          # unit / contract / golden / e2e
```

---

## Quick Start

### One-shot setup

```bash
git clone <repo-url> UAGF_TAM_AAA
cd UAGF_TAM_AAA
python3.12 scripts/setup.py
```

### Fastest offline run

```bash
python -m aaa.cli run \
  --engagement-id eng-uci-german-credit-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

This prints a JSON summary including:

- `final_verdict`
- `intake_completeness_score`
- `completeness_score`
- `regulatory_coverage_pct`
- `art43_decision`
- `phase_artefacts`
- `compliance_matrix`

### Streamlit demo

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

The UI supports:

- Stage A triage editing
- Stage B text fields plus file uploaders
- optional dataset/model uploads
- live completeness preview
- full audit run
- download of PDF, T18 JSON, T17 JSON, and debug AuditState JSON

### FastAPI backend

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Open Swagger at `http://localhost:8000/docs`.

---

## Customer Workflow API

The current minimal API supports the full upload → run → report cycle:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/engagements` | Create engagement |
| `POST` | `/api/v1/engagements/{engagement_id}/files` | Upload a customer file via multipart form |
| `POST` | `/api/v1/engagements/{engagement_id}/intake` | Submit Stage A/B/C payloads |
| `POST` | `/api/v1/engagements/{engagement_id}/run` | Run `IntakeValidator → Orchestrator` |
| `GET` | `/api/v1/engagements/{engagement_id}/report` | Return verdict, KPIs, and report URIs |
| `GET` | `/api/v1/engagements/{engagement_id}/report.pdf` | Return rendered PDF bytes when available |

---

## Regulatory Corpus State

`scripts/ingest_regulatory_corpus.py` currently ingests the following sources into Qdrant:

| Regulation / standard | Chunks |
|-----------------------|--------|
| EU AI Act | **339** |
| GDPR | **288** |
| ISO/IEC 42001:2023 | **88** |
| ISAE 3000 (Revised) | **411** |
| ISO 19011:2018 | **74** |
| **Total** | **1200** |

`obligations_index` additionally contains **15** obligation-question points.

---

## Verification Commands

```bash
pytest -m "not e2e"
python -m pytest \
  tests/unit/test_prompt_registry.py \
  tests/unit/test_client_doc_ingest.py \
  tests/unit/test_regulatory_standards_ingest.py \
  tests/unit/test_materiality_state.py \
  tests/unit/test_remediation_assignment.py \
  tests/unit/test_report_architect_management_response.py \
  tests/unit/test_risk_heatmap_render.py \
  tests/unit/test_maturity_radar_render.py \
  tests/unit/test_auditor_opinion.py \
  tests/unit/test_regulatory_coverage_expanded.py \
  tests/unit/test_evidence_store_file_upload.py \
  tests/unit/test_ui_upload_helpers.py \
  tests/unit/test_api_customer_workflow.py -q
```

---

## Current Project Status

The repository is **tech-complete as a thesis MVP / research prototype**:

- the end-to-end audit pipeline runs
- upload-to-report workflow works in demo form
- the CLI emits a non-null `final_verdict`
- the final report contains structured audit outputs and a downloadable PDF/JSON pair

What remains beyond thesis scope is mostly **production hardening**: branded report rendering, persistent backend storage, authentication, tenancy, and full deployment automation.
