# SETUP.md — Plain-English Setup Guide for AAA

This guide is for someone who wants to **install AAA and run it successfully** without digging through the code first.

AAA can work in three modes:

1. **Streamlit demo** — easiest, point-and-click
2. **CLI demo** — fastest smoke test
3. **FastAPI workflow** — best for integrations

If you want the quickest success path, go straight to **Section 4**.

---

## 1. What you need first

| Tool | Required? | Why |
|------|-----------|-----|
| **Python 3.12** | Yes | The project requires it |
| **git** | Yes | To clone the repository |
| **Docker Desktop** | Optional | Needed only for online/full-service runs |

Check Python:

```bash
python3.12 --version
```

---

## 2. What AAA expects as input

AAA works with three intake stages:

### Stage A — triage

High-level information about the AI system, for example:

- provider name
- system name
- declared modality
- declared risk tier
- declared Annex III sections
- deployment context

### Stage B — Annex IV dossier

Technical and governance evidence, including text fields plus uploaded files such as:

- risk-management file
- EU declaration of conformity
- post-market monitoring plan
- for LLM/agentic systems: system prompt, RAG manifest, guardrail config, golden set
- optional datasets and model artefacts

### Stage C — optional scoped access

Optional read-only live-system access metadata. In offline/demo mode this is usually omitted.

### Ready-made sample input

The repository already includes sample intake files in:

```text
scripts/fixtures/uci_german_credit/
├── stage_a.json
├── stage_b.json
└── stage_c.json
```

These are the easiest way to test the system end-to-end.

---

## 3. Install the project

From the repository root:

```bash
python3.12 scripts/setup.py
```

That script will:

1. create `.venv`
2. install dependencies
3. create `.env` from `.env.example` if needed
4. optionally start Docker services
5. optionally run migrations
6. run a smoke test

If you want a lighter offline-only install:

```bash
python3.12 scripts/setup.py --no-docker --no-migrate
```

Then activate the virtual environment:

```bash
source .venv/bin/activate
```

---

## 4. Fastest ways to run AAA

### Option A — easiest: Streamlit demo

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

What you get — a 5-step guided wizard:

1. **Start** — provide an engagement ID
2. **Upload Documents** — drag-and-drop technical docs, model artefacts, datasets
3. **Quick Questions** — 8 guided questions (role, deployment context, GDPR, Annex III categories, etc.)
4. **Review & Confirm** — `DocIntelligenceAgent` (agent #13, `gpt-5.4`) reads your uploads and pre-fills every Stage A / Stage B field; each auto-filled field shows its source file and confidence score; you edit any field and see the live intake completeness score (gate ≥ 0.80) before confirming
5. **Results** — final verdict, KPI metrics, remediation checklist, compliance matrix, download buttons for:
   - audit report PDF
   - T18 audit report JSON
   - T17 compliance matrix JSON

In offline mode (`AAA_OFFLINE_MODE=true`) the `DocIntelligenceAgent` skips Qdrant ingestion and returns an empty extraction — all fields show "please fill in manually". The wizard still works; you fill the form manually and the audit pipeline runs fully offline.

### Option B — fastest smoke test: CLI

```bash
python -m aaa.cli run \
  --engagement-id eng-uci-german-credit-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

This prints a JSON summary with a final verdict.

### Option C — integration-friendly: FastAPI

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Then open:

```text
http://localhost:8000/docs
```

---

## 5. If you want to upload your own documents

### Easiest path

Use the **Streamlit UI**. It already has upload controls for:

- `risk_management_file_uri`
- `eu_doc_uri`
- `post_market_plan_uri`
- `system_prompt_uri`
- `rag_manifest_uri`
- `guardrail_config_uri`
- `golden_set_uri`
- `training_dataset_uri`
- `evaluation_dataset_uri`
- `model_artifact_uri`
- `model_metadata_uri`

You do **not** need to manually create `minio://...` URIs. The UI stores files in the in-memory `EvidenceStore` for you.

### API path

Use this order:

1. create engagement
2. upload files
3. submit intake JSON with returned URIs
4. run engagement
5. fetch report / report PDF

Example endpoints:

| Method | Path |
|--------|------|
| `POST` | `/api/v1/engagements` |
| `POST` | `/api/v1/engagements/{engagement_id}/files` |
| `POST` | `/api/v1/engagements/{engagement_id}/intake` |
| `POST` | `/api/v1/engagements/{engagement_id}/run` |
| `GET` | `/api/v1/engagements/{engagement_id}/report` |
| `GET` | `/api/v1/engagements/{engagement_id}/report.pdf` |

---

## 6. Optional: load the full regulatory corpus into Qdrant

You only need this for **online / real retrieval mode**.

### Start Qdrant

```bash
docker compose up -d qdrant
```

### Dry run the ingestion first

```bash
python3.12 scripts/ingest_regulatory_corpus.py --dry-run -v
```

Current dry-run totals:

- EU AI Act: **339** chunks
- GDPR: **288** chunks
- ISO/IEC 42001: **88** chunks
- ISAE 3000: **411** chunks
- ISO 19011: **74** chunks
- total corpus: **1200** chunks

### Full ingestion

```bash
python3.12 scripts/ingest_regulatory_corpus.py \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

The script is idempotent: re-running it does not re-embed unchanged chunks.

---

## 7. Important settings in `.env`

| Variable | What it controls |
|----------|------------------|
| `AAA_OFFLINE_MODE` | Set `true` for offline/demo mode |
| `AAA_LOG_LEVEL` | Logging verbosity |
| `OPENAI_API_KEY` / other LLM keys | Needed for online LLM execution |
| `QDRANT_URL` | Qdrant server |
| `CGSA_FIXTURE_DIR` | Offline CGSA fixtures |
| `S4_CGSA_BASE_URL` | Online S4 endpoint |

If you are unsure, leave the defaults and start with offline mode.

---

## 8. What you receive at the end of a run

AAA produces:

- a **final verdict** (`PASS`, `PASS_WITH_OBSERVATIONS`, or `FAIL`)
- KPI scores
- compliance matrix (`T17`)
- final audit report (`T18`)
- a rendered **PDF report** when ReportLab output is available

The final report includes the latest additions:

- auditor opinion
- management response shell
- remediation roadmap with owners/priorities
- risk heat-map
- maturity radar

---

## 9. If something goes wrong

Try these in order:

1. activate the virtual environment again
2. re-run `python3.12 scripts/setup.py`
3. force offline mode: `export AAA_OFFLINE_MODE=true`
4. if using Docker, restart services:

```bash
docker compose down -v
docker compose up -d
```

Common issues:

| Problem | Fix |
|--------|-----|
| `python3.12: command not found` | Install Python 3.12 |
| `ModuleNotFoundError` | Activate `.venv` |
| Qdrant/OpenAI errors during corpus ingestion | Use offline mode first, or set the missing keys/services |
| No PDF available | The JSON report is still produced; PDF rendering is best-effort |

For the full developer/operator guide, read [`USER_MANUAL.md`](./USER_MANUAL.md).
