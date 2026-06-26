# AAA — Autonomous AI Auditor

AAA is a modular EU AI Act audit system built around a **13-agent pipeline**, a
FastAPI integration surface, a Streamlit demo UI, structured observability, and
a lightweight file-based persistence layer for demo and thesis workflows.

> **Python 3.12 is required.**

## Current codebase snapshot

The repository currently includes:

- a modular FastAPI app in `aaa/api/` with route files for health, engagements,
  workflow, reports, and persisted data access
- a modular tier-1 orchestrator in `aaa/agents/tier1/phases/`
- structured logs and LLM audit trails in `aaa/observability/`
- a local JSON persistence layer in `aaa/data/` controlled by `AAA_DATA_DIR`
- Dagster assets, jobs, and sensors in `aaa/dagster/`
- unit, contract, golden, and placeholder e2e tests in `tests/`

## Audit methodology — evidence-grounded, not rubber-stamped

AAA performs an **independent** audit: it does not trust the provider's declared
numbers. For each engagement it

- **loads the real artefacts** uploaded in Stage B (the fitted model, the
  training/evaluation datasets, the governance `.docx` documents) and **re-runs** the
  analysis tools on them — performance metrics, robustness probes, the fairness suite,
  data-quality/PII scans — then diffs the recomputed results against the declared
  `accuracy_metrics`;
- routes every phase artefact through an **independent Verifier** before it is admitted;
- **grounds each article verdict in evidence** with a per-article rationale and evidence
  URIs. Article verdicts are `PASS`, `PASS_WITH_OBSERVATIONS`, `FAIL`, or
  `INSUFFICIENT_EVIDENCE` — **absence of evidence is never `PASS`**. A non-executable model
  or an unretrievable governance self-assessment yields `INSUFFICIENT_EVIDENCE`, not a pass.
- issues an ISAE-3000-style **auditor opinion**: `unqualified`, `qualified`, `adverse`
  (confirmed non-conformity), or `disclaimer_of_opinion` (a mandatory high-risk requirement
  could not be verified).

See [ARCHITECTURE.md §3.2a](./ARCHITECTURE.md) for the full verdict ladder.

## Documentation

| File | Purpose |
|------|---------|
| [USER_MANUAL.md](./USER_MANUAL.md) | End-user walkthrough for offline and online runs. |
| [SETUP.md](./SETUP.md) | Technical quick-start, environment variables, and verification commands. |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Full system design and thesis-oriented architecture notes. |
| [PROMPT.md](./PROMPT.md) | Canonical prompt source for the runtime prompt registry. |
| [infra/runbook.md](./infra/runbook.md) | Current operational procedures for the implemented repo. |

## Quick start

### 1. Bootstrap the environment

```bash
python3.12 scripts/setup.py --no-docker --no-migrate
source .venv/bin/activate
```

### 2. Run the offline Streamlit demo

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

Open `http://localhost:8501`.

### 3. Run the offline CLI smoke path

```bash
AAA_OFFLINE_MODE=true \
python -m aaa.cli run \
  --engagement-id eng-demo-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

### 4. Run the API

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

## Main surfaces

| Surface | Command | Notes |
|---------|---------|-------|
| Streamlit UI | `streamlit run aaa/ui/app.py` | 5-step wizard for upload, intake, and results. |
| CLI | `python -m aaa.cli run ...` | Smallest end-to-end smoke path. |
| FastAPI | `uvicorn aaa.api.main:app --reload --port 8000` | REST API with health, workflow, report, and data endpoints. |
| Dagster | `dagster dev -m aaa.dagster.definitions` | Monitoring and asset orchestration entry point. |

## What is persisted locally

By default, AAA writes repo-local JSON data under `data/`.

| Path | Contents |
|------|----------|
| `data/index.json` | Master index of stored engagements |
| `data/inputs/<engagement_id>/engagement.json` | Engagement creation metadata |
| `data/inputs/<engagement_id>/intake.json` | Stage A/B/C payload submitted by the user |
| `data/inputs/<engagement_id>/files.json` | Uploaded-file metadata list |
| `data/results/<engagement_id>/audit_result.json` | Final verdict and KPI summary |
| `data/results/<engagement_id>/artefacts.json` | Phase artefact references |
| `data/results/<engagement_id>/findings.json` | Blocking and positive findings |
| `data/results/<engagement_id>/compliance_matrix.json` | Article-by-article compliance output |

Change the root with `AAA_DATA_DIR=/path/to/data-root`.

## Observability and monitoring

AAA now emits structured logs and explicit LLM audit records.

| Path | Contents |
|------|----------|
| `logs/app/app.log` | Root application log |
| `logs/api/api.log` | FastAPI route activity |
| `logs/agents/agents.log` | Agent/runtime logs |
| `logs/audit/llm_audit.log` | Structured audit log stream |
| `logs/audit/llm_audit.jsonl` | One JSON record per LLM call: prompt, reply, tokens, latency, cost |
| `logs/errors/*.jsonl` | Error records written by `capture_error(...)` |
| `logs/dagster/dagster.log` | Dagster runtime logs |

Prometheus metrics are exposed at `GET /metrics`.

## REST API summary

### Health and ops

| Method | Path |
|--------|------|
| `GET` | `/healthz` |
| `GET` | `/api/v1/schema-version` |
| `GET` | `/metrics` |

### Engagement workflow

| Method | Path |
|--------|------|
| `GET` | `/api/v1/engagements` |
| `POST` | `/api/v1/engagements` |
| `GET` | `/api/v1/engagements/{engagement_id}` |
| `POST` | `/api/v1/engagements/{engagement_id}/files` |
| `POST` | `/api/v1/engagements/{engagement_id}/extract-triage` |
| `POST` | `/api/v1/engagements/{engagement_id}/intake` |
| `POST` | `/api/v1/engagements/{engagement_id}/run` |
| `GET` | `/api/v1/engagements/{engagement_id}/report` |
| `GET` | `/api/v1/engagements/{engagement_id}/report.pdf` |

### Persistent data access

| Method | Path |
|--------|------|
| `GET` | `/api/v1/data/engagements` |
| `GET` | `/api/v1/data/results` |
| `GET` | `/api/v1/data/engagements/{engagement_id}/input` |
| `GET` | `/api/v1/data/engagements/{engagement_id}/result` |

## Repository layout

```text
UAGF_TAM_AAA/
├── aaa/
│   ├── agents/            # 13-agent system + orchestrator phase modules
│   ├── api/               # FastAPI app, schemas, in-memory runtime store, routers
│   ├── dagster/           # assets, jobs, sensors, definitions
│   ├── data/              # file-based persistence layer
│   ├── observability/     # logging, metrics, error capture, LLM audit
│   ├── platform/          # prompt registry, evidence store, state, model registry
│   ├── tools/             # deterministic audit tools
│   └── ui/                # Streamlit wizard
├── data/                  # persisted demo data + regulatory corpus + fixtures
├── infra/                 # runbook + tofu infrastructure files
├── packages/              # distributable schema package(s)
├── scripts/               # setup, demo, ingestion, fixtures
├── templates/             # canonical T01a–T18 schemas in repo root
└── tests/                 # unit, contract, golden, e2e-placeholder tests
```

## Regulatory corpus

The repo ships the source materials under `data/regulatory_corpus/`. To enable
live retrieval, start Docker services and run:

```bash
python3.12 scripts/ingest_regulatory_corpus.py --dry-run -v
python3.12 scripts/ingest_regulatory_corpus.py \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

For more detail, see [SETUP.md](./SETUP.md) and [USER_MANUAL.md](./USER_MANUAL.md).
