# SETUP.md — Technical Quick Start

This guide reflects the **current implemented repository**. Use it when you want
the fastest path to get AAA installed, verified, and running.

## 1. Prerequisites

| Requirement | Needed for | Notes |
|-------------|------------|-------|
| Python 3.12 | everything | required by the repo |
| git | cloning / updates | standard development tool |
| Docker Desktop | online retrieval + full local stack | optional for offline/demo use |

Verify Python:

```bash
python3.12 --version
```

## 2. Fastest install path

From the repository root:

```bash
python3.12 scripts/setup.py --no-docker --no-migrate
source .venv/bin/activate
```

What `scripts/setup.py` does:

1. creates `.venv`
2. installs dependencies
3. creates `.env` from `.env.example` if missing
4. optionally starts Docker services
5. optionally runs Alembic migrations
6. runs an offline smoke test

If you want the heavier online/full-stack bootstrap instead, run:

```bash
python3.12 scripts/setup.py
```

## 3. Verify the installation

Run the small offline verification path (includes `tests/unit/test_real_auditor.py`,
which locks in the evidence-grounded verdict ladder — FAIL / INSUFFICIENT_EVIDENCE /
disclaimer):

```bash
AAA_OFFLINE_MODE=true python -m pytest tests/unit -q
```

Then check the CLI help and API import path:

```bash
python -m aaa.cli --help
python -c "from aaa.api.main import app; print(app.title)"
```

> **Independent verification inputs.** The audit re-runs analysis on the *real* artefacts
> rather than trusting declared metrics. To exercise this, an engagement's Stage B should
> carry `model_artifact_uri`, `evaluation_dataset_uri`, and `training_dataset_uri` (the UI
> upload flow sets these), plus an optional data dictionary (`target_column`,
> `positive_label`, `sensitive_feature_columns`). A missing/non-executable model or
> unreadable dataset yields `INSUFFICIENT_EVIDENCE` for the affected articles — never PASS.

## 4. Run the repo

### Streamlit demo

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

### CLI smoke path

```bash
AAA_OFFLINE_MODE=true \
python -m aaa.cli run \
  --engagement-id eng-demo-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

### FastAPI

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Useful URLs:

- Swagger UI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/healthz`
- Metrics: `http://localhost:8000/metrics`

### Dagster

```bash
dagster dev -m aaa.dagster.definitions
```

This loads the current assets, jobs, sensors, and schedules from `aaa/dagster/`.

## 5. Current environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AAA_OFFLINE_MODE` | disable external-service-dependent execution paths | `false` |
| `AAA_LOG_LEVEL` | Python/structlog verbosity | `WARNING` |
| `AAA_DATA_DIR` | root directory for persisted input/result JSON | `data` |
| `AAA_LOG_DIR` | root directory for structured logs | `logs` |
| `CGSA_FIXTURE_DIR` | offline CGSA fixture source. If unset/unreachable offline, the CGSA self-assessment can't be pulled and the governance articles (Art.9/12/17/72) are marked `INSUFFICIENT_EVIDENCE` (not a hard FAIL). | empty |
| `CGSA_SCHEMA_VERSION` | pinned CGSA version exposed by the API | `1.0.0` |
| `OPENAI_API_KEY` | online LLM execution | empty |
| `QDRANT_URL` | vector store for regulatory/document retrieval | repo `.env` default |
| `S4_CGSA_BASE_URL` | S4 integration base URL | `http://localhost:8001` |

## 6. Current persistence layout

AAA now persists user-entered inputs and audit results to a local JSON store.

```text
data/
  index.json
  inputs/
    <engagement_id>/
      engagement.json
      intake.json
      files.json
  results/
    <engagement_id>/
      audit_result.json
      artefacts.json
      findings.json
      compliance_matrix.json
```

Notes:

- `files.json` stores uploaded-file metadata, not raw file bytes
- runtime engagement state in `aaa/api/store.py` is still in-memory for the live
  FastAPI process
- the EvidenceStore used for uploaded/report artefacts is still in-memory in the
  current thesis/demo implementation

## 7. Current observability layout

```text
logs/
  app/app.log
  api/api.log
  agents/agents.log
  audit/llm_audit.log
  audit/llm_audit.jsonl
  dagster/dagster.log
  errors/*.jsonl
```

`logs/audit/llm_audit.jsonl` is the most important file for LLM accountability.
Each record includes the request messages, response text, token usage, latency,
and estimated cost when available.

## 8. FastAPI route map

### Core ops

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/healthz` | liveness + schema version |
| `GET` | `/api/v1/schema-version` | pinned schema version |
| `GET` | `/metrics` | Prometheus text exposition |

### Engagement workflow

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/engagements` | list engagements |
| `POST` | `/api/v1/engagements` | create engagement |
| `GET` | `/api/v1/engagements/{id}` | get engagement |
| `POST` | `/api/v1/engagements/{id}/files` | upload file |
| `POST` | `/api/v1/engagements/{id}/extract-triage` | run doc extraction |
| `POST` | `/api/v1/engagements/{id}/intake` | submit intake payload |
| `POST` | `/api/v1/engagements/{id}/run` | run pipeline |
| `GET` | `/api/v1/engagements/{id}/report` | JSON result summary |
| `GET` | `/api/v1/engagements/{id}/report.pdf` | rendered PDF if available |

### Data-store routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/data/engagements` | persisted engagement index |
| `GET` | `/api/v1/data/results` | completed engagements |
| `GET` | `/api/v1/data/engagements/{id}/input` | all stored input data |
| `GET` | `/api/v1/data/engagements/{id}/result` | full stored result |

## 9. Online mode extras

If you want live retrieval and non-demo execution paths:

1. start Docker services
2. populate `.env` with the required provider keys
3. run Alembic if you want the optional Postgres schema available
4. ingest the regulatory corpus into Qdrant

Commands:

```bash
docker compose up -d
python -m alembic upgrade head
python3.12 scripts/ingest_regulatory_corpus.py --dry-run -v
python3.12 scripts/ingest_regulatory_corpus.py \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

## 10. Troubleshooting quick hits

| Problem | Recommended first step |
|--------|-------------------------|
| `python3.12` missing | install Python 3.12 |
| `ModuleNotFoundError` | reactivate `.venv` |
| API imports fail | run `source .venv/bin/activate` and retry |
| No PDF returned | inspect `/api/v1/engagements/{id}/report`; JSON output may still be available |
| Missing online retrieval | confirm Docker is running and corpus ingestion completed |
| Need to inspect persisted outputs | look under `data/results/<engagement_id>/` or use `/api/v1/data/...` |

For the end-user walkthrough, see [`USER_MANUAL.md`](./USER_MANUAL.md).
