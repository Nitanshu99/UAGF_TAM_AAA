# SETUP.md — Technical Quick Start

This guide reflects the **current implemented repository**. Use it when you want
the fastest path to get AAA installed, verified, and running.

## 1. Prerequisites

| Requirement | Needed for | Notes |
|-------------|------------|-------|
| Python 3.12 | everything | required by the repo |
| git | cloning / updates | standard development tool |
| Docker Desktop | live retrieval + full local stack | optional for the laptop-only demo |

Verify Python:

```bash
python3.12 --version
```

## 2. Fastest install path

### 2a. Everything, in one command

With `mariposa.zip` and `corpus.zip` in the repository root and an OpenRouter
key at hand:

```bash
python3.12 bootstrap.py            # or: make bootstrap
```

Ten idempotent steps: Python 3.12 + `.venv`; dependencies (skipped when the
requirement files are unchanged); Docker and the two bundles present; `.env`
(created from `.env.example`, `PROVIDER=openrouter` and all three
`EMBEDDINGS_*=openrouter`, vendor placeholders blanked, Langfuse provisioned
with generated keys on a fresh file, and — where blank — the reference model
configuration `OPENROUTER_MODEL=minimax/minimax-m3`, `OPENROUTER_PROVIDER=coreweave/fp4`
that reproduces the published Mariposa result; `OPENROUTER_PROVIDER=none` chooses
the free route); bundles unpacked to
`mock/06_mariposa_edu_gmbh/` and `data/`; `docker compose --profile obs
--profile ui up -d --wait` plus Alembic; `playwright install chromium`; the
corpus embedded into Qdrant (skipped when already there from the same
embedder, rebuilt when built by another); API + UI health-checked; one
Chromium window with every service dashboard in a tab — MinIO, Grafana (as
admin) and Langfuse signed in with the credentials from `.env` — and the
wizard in front, filled and dispatched, held open until you close it or press
Ctrl-C. The Docker
stack stays up afterwards: `docker compose --profile obs --profile ui down`.

`--mock-llm` runs the identical path against a local stub (deterministic
embeddings, chat refused, so every agent takes its deterministic fallback) and
spends nothing; `--no-run` fills the form without dispatching; `--screenshots
DIR` saves a PNG of every tab and of the form/results; `--help` lists the rest.
Ports are the compose defaults unless overridden in `.env` (see §8).

### 2b. Laptop-only checkout

From the repository root:

```bash
python3.12 -m scripts.setup --no-docker --no-migrate
source .venv/bin/activate
```

What `python -m scripts.setup` does (each step is idempotent):

1. verifies Python ≥ 3.12
2. creates `.venv`
3. upgrades pip and installs dependencies
4. creates `.env` from `.env.example` if missing
5. optionally starts Docker services (`--no-docker` to skip)
6. optionally runs Alembic migrations (`--no-migrate` to skip)
7. runs a pytest smoke test (`--no-tests` to skip)

For the heavier full-stack bootstrap (Docker + migrations), drop the flags:

```bash
python3.12 -m scripts.setup
```

## 3. Run the whole stack with one command

After the bootstrap, a single command starts every configured component —
Docker infrastructure, migrations, the FastAPI backend, and the Streamlit UI:

```bash
make start        # or:  python -m aaa   (or the `aaa` console script)
```

The launcher's plan is read from `.env`:

| Variable | Default | Effect |
|----------|---------|--------|
| `AAA_LAUNCH_DOCKER` | `auto` | Start Docker Compose infra (`auto`/`true`/`false`). |
| `AAA_LAUNCH_MIGRATE` | `auto` | Run Alembic migrations on start. |
| `AAA_LAUNCH_API` | `true` | Start the FastAPI backend. |
| `AAA_LAUNCH_UI` | `true` | Start the Streamlit UI. |
| `PLATFORM_PORT` | `8000` | FastAPI port. |
| `STREAMLIT_SERVER_PORT` | `8501` | Streamlit port. |

Run a single surface instead of the whole stack:

```bash
aaa ui                          # Streamlit wizard only
aaa api                         # FastAPI backend only
aaa audit --engagement-id ...   # headless CLI audit of a fixture
```

## 4. Verify the installation

Run the unit suite (includes the `test_real_auditor_*` files, which lock in the
evidence-grounded verdict ladder — FAIL / INSUFFICIENT_EVIDENCE / disclaimer):

```bash
python -m pytest tests/unit -q
```

Then check the CLI help and API import path:

```bash
python -m aaa.cli --help
python -c "from aaa.api.main import app; print(app.title)"
```

> **Independent verification inputs.** The audit re-runs analysis on the *real*
> artefacts rather than trusting declared metrics. To exercise this, an
> engagement's Stage B should carry `model_artifact_uri`,
> `evaluation_dataset_uri`, and `training_dataset_uri` (the UI upload flow sets
> these), plus an optional data dictionary (`target_column`, `positive_label`,
> `sensitive_feature_columns`). A missing/non-executable model or unreadable
> dataset yields `INSUFFICIENT_EVIDENCE` for the affected articles — never PASS.
> Generative systems usually have no artefact to upload; they declare
> `model_access_mode` and a `model_reference` naming the vendor model instead,
> and the report records that metrics were not recomputed from weights rather
> than treating the absence as a missing upload.

## 5. Run individual surfaces

### Streamlit wizard

```bash
CGSA_FIXTURE_DIR=mock:scripts/fixtures/cgsa streamlit run aaa/ui/app.py
```

### Headless CLI audit

```bash
python -m aaa.cli run \
  --engagement-id eng-demo-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa
```

### FastAPI

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Useful URLs: Swagger UI `http://localhost:8000/docs`, health
`http://localhost:8000/healthz`, metrics `http://localhost:8000/metrics`.

## 6. Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AAA_LAUNCH_DOCKER` / `_MIGRATE` / `_API` / `_UI` | one-command launcher plan (see §3) | `auto`/`auto`/`true`/`true` |
| `AAA_LOG_LEVEL` | Python/structlog verbosity | `WARNING` |
| `AAA_DATA_DIR` | root directory for persisted input/result JSON | `data` |
| `AAA_LOG_DIR` | root directory for structured logs | `logs` |
| `CGSA_FIXTURE_DIR` | Path-separated search order for CGSA exports, most specific root first. If unset/unreachable, the governance articles (Art.9/12/17/72) are marked `INSUFFICIENT_EVIDENCE` (not a hard FAIL). | `mock:scripts/fixtures/cgsa` |
| `AAA_CGSA_FIXTURE_DIR` | Overrides the above outright — for a real S5 export held outside the repo. | empty |
| `CGSA_SCHEMA_VERSION` | pinned CGSA version exposed by the API | `1.0.0` |
| `PROVIDER` | active LLM provider: unset/`openai` uses the GPT-5.6 roster, `nvidia` redirects the whole 14-agent roster to NVIDIA NIM (`nvidia_roster.py`), `openrouter` redirects it to OpenRouter (`openrouter/roster.py`). **`openrouter` is what this repo's `.env` ships** — NVIDIA NIM's free tier exhausted mid-run on 2026-09-09 (34 of 54 calls failed) while the same roster model answered in 14 s over OpenRouter | `openai` |
| `OPENAI_API_KEY` | LLM execution; LiteLLM reads it (+ `OPENAI_API_BASE` for a gateway/Azure) to route the `gpt-5.6-*` models in `model_registry`. Without it, agents fall back to deterministic paths. | empty |
| `NVIDIA_API_KEY` | LLM execution when `PROVIDER=nvidia`; propagated into `NVIDIA_NIM_API_KEY` for LiteLLM's `nvidia_nim/` prefix | empty |
| `OPENROUTER_API_KEY` | LLM execution when `PROVIDER=openrouter`; read directly by LiteLLM's `openrouter/` prefix, no aliasing needed. Also the key of the `openrouter` embedding provider and, under this provider, of the RAGAs judge — one key for everything | empty |
| `OPENROUTER_API_BASE` | OpenRouter's API root for both LiteLLM and the `openrouter` embedder; unset = the public gateway. `bootstrap.py --mock-llm` points it at a local stub | `https://openrouter.ai/api/v1` |
| `EMBEDDINGS_CLIENT_DOCS` / `_REGULATORY` / `_EVIDENCE` | embedding provider per purpose: `openai`, `openrouter` or `local` (§8) | `openai` |
| `AAA_ORCHESTRATION_MODE` | `react` (LLM-decided sequencing, the production path) or `graph` (deterministic LangGraph fallback). Unset ⇒ `react` whenever a provider key is present. | unset |
| `AAA_DISABLE_FLEX` | when `true`, agents send no `service_tier="flex"` — use for backends that don't support OpenAI Flex processing | `false` |
| `QDRANT_URL` | vector store for regulatory/document retrieval | repo `.env` default |
| `S4_CGSA_BASE_URL` | S4 integration base URL | `http://localhost:8001` |
| `S6_XAI_MODE` | explainability/fairness provider: `internal` (built-in SHAP/LIME/fairness tools) or `external` (POST the audit-state hand-off to the S6 API) | `internal` |
| `S6_XAI_BASE_URL` / `S6_XAI_BEARER_TOKEN` | external S6 service root + optional auth | `http://localhost:8006` / empty |
| `S7_SEC_MODE` | security/robustness provider, switched independently of S6 | `internal` |
| `S7_SEC_BASE_URL` / `S7_SEC_BEARER_TOKEN` | external S7 service root + optional auth | `http://localhost:8007` / empty |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | **project** API keys (create a project at `http://localhost:3003` after first start-up, then paste its keys here) — turns on real LLM tracing. Blank = tracing stays off (a no-op, not an error). See §8. | empty (tracing off) |
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana admin password (`obs` profile only, §8) | `admin` |

> **Running the bundled mock cases:** `python -m scripts.run_mock_case <case>`
> — five domain cases ship: `01_finclear_gmbh` (finance, tabular),
> `02_retailiq_ag` (retail forecasting, time-series),
> `03_harbourlogistik_gmbh` (critical infrastructure, tabular),
> `04_legalmindd_ai_ltd` (LLM+RAG, agentic) and
> `05_talentsift_gmbh` (CV screening, nlp). Each is self-contained — it loads `.env`, auto-wires
> `CGSA_FIXTURE_DIR` from `mock/<case>/cgsa`, runs the full pipeline, prints
> whether the LLM harness fired (ok vs error per agent, from
> `logs/audit/llm_audit.jsonl`), and saves `audit_state` + T17 + T18 to
> `data/customer/<company>/`.

## 7. Persistence layout

AAA persists user-entered inputs and audit results to a local JSON store.

```text
data/
  index.json
  inputs/<engagement_id>/{engagement,intake,files}.json
  results/<engagement_id>/{audit_result,artefacts,findings,compliance_matrix}.json
  customer/<company>/<id>_{audit_state,T17,T18,hitl_review}.json
```

Notes:

- `files.json` stores uploaded-file metadata, not raw file bytes
- runtime engagement state in `aaa/api/store.py` is in-memory for the live
  FastAPI process
- the EvidenceStore used for uploaded/report artefacts is in-memory in the
  current thesis/demo implementation

## 8. Observability layout

```text
logs/
  app/app.log
  api/api.log
  agents/agents.log
  audit/llm_audit.log
  audit/llm_audit.jsonl
  errors/*.jsonl
```

`logs/audit/llm_audit.jsonl` is the most important file for LLM accountability
and is **always** written, regardless of any other observability config. Each
record includes the request messages, response text, token usage, latency,
and estimated cost when available. Read it directly (`cat logs/audit/llm_audit.jsonl | jq`)
or query it live through Loki (see below).

**Langfuse (LLM tracing — real, not just provisioned).** Langfuse v4 runs as
two containers plus ClickHouse: `langfuse` (web, port `3003`) accepts the OTEL
POST and queues it through Valkey and a MinIO bucket, and `langfuse-worker`
drains that queue into ClickHouse. All of it starts with the core stack
(`docker compose up`). Set `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` in
`.env` **before the first start**: the container provisions its org, project
and API keys from those same values (`LANGFUSE_INIT_*`, see `.env.example`),
together with the web-UI login (`LANGFUSE_INIT_USER_EMAIL` /
`LANGFUSE_INIT_USER_PASSWORD` — sign in at `http://localhost:3003` with those). There is no "create a project, copy its keys"
step, and the server and the app cannot disagree about the keys. Blank keys
leave tracing a no-op (the containers run, nothing is sent). Once configured,
every LLM call across the pipeline becomes a Langfuse generation, and every
call made during one engagement groups into a single session (search by the
engagement id in the Langfuse UI). Langfuse v4 runs in *events_only* mode:
the legacy `/api/public/traces` and `/sessions` endpoints answer 404 — use
`/api/public/v2/observations?sessionId=<engagement id>` from scripts.

Check the ingest path end to end without spending a token:

```bash
python -m scripts.obs_probe        # one mock LLM call through the audited wrapper
```

It exercises the same seam a real call uses — `write_audit` (metrics +
`llm_audit.jsonl`) and the `langfuse_otel` callback — and then verifies the
call arrived in Prometheus (`/metrics`), in Loki and in Langfuse's public API.

> A leftover placeholder such as `LANGFUSE_SECRET_KEY=changeme` from an older
> `.env` counts as **not configured**: it is non-empty, so it used to switch
> tracing on with credentials that were never valid, failing at every export
> rather than at start-up. Placeholders are now ignored, with a warning.

> Server-side secrets are separate variables — `LANGFUSE_SALT`,
> `LANGFUSE_NEXTAUTH_SECRET`, `LANGFUSE_ENCRYPTION_KEY` — not the project
> keys. Changing them invalidates existing Langfuse web-UI logins; harmless
> for local dev.

**Embeddings are chosen per purpose.** `EMBEDDINGS_CLIENT_DOCS`,
`EMBEDDINGS_REGULATORY` and `EMBEDDINGS_EVIDENCE` each take `openai` (default),
`openrouter` or `local`. They are independent so the customer's own compliance
dossier can be embedded on this host while the public EU-law corpus keeps a
hosted model's retrieval quality. `openrouter` is the same
`text-embedding-3-large` (3072-dim) reached through OpenRouter's
OpenAI-compatible gateway with `OPENROUTER_API_KEY` — one key for the agent
roster and retrieval, which is what `bootstrap.py` configures; the identity
stamp records the gateway (`openrouter:openai/text-embedding-3-large`, or
`openrouter@<host>:…` when `OPENROUTER_API_BASE` points elsewhere), so a
corpus built through the `--mock-llm` stub is rebuilt on the next real run
rather than searched. `local` requires naming a model in
`EMBEDDINGS_LOCAL_MODEL` — there is no default, because that choice fixes a
quality/size trade-off.

**Client documents are re-embedded on every run.** A returning engagement is
assumed to have updated its dossier, so the per-engagement Qdrant collection is
dropped before the first ingest of each run rather than appended to — otherwise
a superseded document would keep matching searches indefinitely. The reset
happens once per process, not once per call, because `client_doc_ingest` is
invoked twice in a single pipeline (by `ingest_documents()` at upload time and
by the `IntakeValidator`); both callers contribute to the same fresh
collection. A reset failure logs a warning and continues, since the worst case
is keeping the previous run's vectors.

Changing `EMBEDDINGS_REGULATORY` **invalidates the ingested corpus**: providers
emit different vector widths (OpenAI's large model 3072, typical SBERT models
384 or 768), so the collection must be rebuilt:

```bash
python -m scripts.ingest_regulatory_corpus --reset
```

Until it is, `RegulatoryRAG` refuses the search rather than returning
confidently-ranked nonsense. Ingestion stamps the embedding model's identity
into a sibling `<collection>__embedding_meta` collection, so the check is exact:
swapping between two *same-width* models is caught too, not just a change in
dimensionality. A corpus ingested before stamping existed carries no stamp — it
still searches, falling back to the width check, with a warning that the model
itself could not be verified.

**Upgrading an existing deployment.** Langfuse now uses its own `langfuse`
database *and role* rather than the application superuser on `${POSTGRES_DB}`.
The init script only runs on an empty Postgres volume, so on an existing
cluster create both once by hand (password = `LANGFUSE_POSTGRES_PASSWORD`),
then recreate the stack so the new images and settings apply:

```bash
docker compose exec postgres psql -U aaa -c "CREATE ROLE langfuse LOGIN PASSWORD '<LANGFUSE_POSTGRES_PASSWORD>'"
docker compose exec postgres psql -U aaa -c 'CREATE DATABASE langfuse OWNER langfuse'
docker compose --profile obs up -d --remove-orphans
```

If the database already exists and is owned by `aaa`, hand it over instead
(`ALTER DATABASE langfuse OWNER TO langfuse`, then `ALTER TABLE/SEQUENCE/TYPE
… OWNER TO langfuse` for every object in its `public` schema).

**MinIO credentials.** `minio-init` (`infra/minio/init.sh`) creates one
service account per bucket: `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY` for the
app (policy `evidence-rw`: read/write/list on `aaa-evidence`, no delete) and
`LANGFUSE_S3_ACCESS_KEY`/`LANGFUSE_S3_SECRET_KEY` for Langfuse (policy
`langfuse-rw` on the `langfuse` bucket). Leave them blank to fall back to the
root key in local dev; set them (any value ≥ 8 chars) and re-run
`docker compose up -d minio-init` to provision. The root key never leaves the
server after that.

A deployment that ran the old `langfuse/langfuse:2` image against
`${POSTGRES_DB}` still carries its 40 Prisma tables there.
`infra/postgres/drop-legacy-langfuse-v2.sql` removes them; it prints the
legacy row counts first and is never run automatically.

**Prometheus + Grafana + Loki (metrics, dashboards, log search — optional).**
Not part of the default `docker compose up`; start with `make obs` (equivalent
to `docker compose --profile obs up -d`). Adds:

| Service | Where | What you get |
|---|---|---|
| Grafana | `http://localhost:3002` | Single pane over everything below — anonymous Viewer access for local dev (admin login: `admin` / `GF_SECURITY_ADMIN_PASSWORD`). Ships with the provisioned "AAA — Audit Pipeline Overview" dashboard: API scrape health, LLM calls/cost/latency/tokens by agent and model, error ratio, phase latency and outcomes, engagements by verdict, log volume by level, and two log panels (errors/warnings; LLM-call audit). |
| Prometheus | `127.0.0.1:9090` (localhost only) | Scrapes the FastAPI `/metrics` endpoint plus Loki, Alloy, Grafana and itself; 90-day retention (`PROMETHEUS_RETENTION`); evaluates `infra/observability/rules/aaa-alerts.yml` (API scrape down, LLM error ratio, captured errors, intake failures, dropped log entries) — visible on `/alerts`. |
| Loki | internal only, reached via Grafana | Log search over everything Alloy ships; 90-day retention via the compactor. Labels are deliberately few: `job`, `filename`, `level`, `ts_source` (`record` when the line carried its own timestamp, `ingest` for pre-timestamp history indexed at read time), and for LLM-call rows `agent` and `status`. Filter on engagement with `{job="aaa"} \| json \| engagement_id="eng-…"`. |
| Alloy | `127.0.0.1:12345` (pipeline/debug UI) | Tails every file under `logs/**` (`*.log` and `*.jsonl`), stamps each entry with the record's own timestamp, extracts `level`, and projects `llm_audit.jsonl` rows down to their metadata (agent, model, status, latency, tokens, cost) — the full prompt and reply stay in the file and in Langfuse. Read positions persist across container recreates. |

**Metrics from every process.** Prometheus only scrapes the API, but the
pipeline runs in whichever process invoked it (Streamlit wizard, `aaa.cli`,
`scripts.run_mock_case`). `import aaa` therefore switches `prometheus_client`
into multiprocess mode with a shared directory (`logs/metrics`, or
`PROMETHEUS_MULTIPROC_DIR`), and the API's `/metrics` renders the merged view
— so a run from the wizard shows up on the dashboard exactly like an API run.
The per-process `*.db` files there are the counters themselves; deleting the
directory resets the dashboard to zero.

`make obs-down` stops just these four; the core stack (Postgres, Qdrant,
MinIO, Valkey, Langfuse, OpenBao) is unaffected either way.

Two more dashboards ship in the provisioned Grafana folder: the overview above
and **AAA — Logs (Loki)** (`/d/aaa-logs`), a level/search-filtered view of
everything Alloy ships — Loki's own tab in the bootstrap's browser, since Loki
has no UI and Explore is not open to the anonymous Viewer.

**Service UIs (`ui` profile — `make ui`, or the bootstrap).** Postgres and
Valkey have no UI of their own, so the profile adds `pgweb`
(`http://127.0.0.1:8081`, connected to the app database from the same
credentials) and `redis-commander` (`http://127.0.0.1:8082`, on the Langfuse
queue). Both bind to loopback only.

**Host ports.** Every published port in `docker-compose.yml` is
`${X_PORT:-default}` — `QDRANT_PORT`, `MINIO_PORT`, `MINIO_CONSOLE_PORT`,
`VALKEY_PORT`, `LANGFUSE_PORT`, `OPENBAO_PORT`, `PROMETHEUS_PORT`,
`ALLOY_PORT`, `GRAFANA_PORT`, `PGWEB_PORT`, `REDIS_COMMANDER_PORT` next to the
existing `POSTGRES_PORT` — so two checkouts can run side by side from their own
`.env` (with `COMPOSE_PROJECT_NAME` set). Move the app-side addresses with them:
`DATABASE_URL`, `QDRANT_URL`, `MINIO_ENDPOINT`, `REDIS_URL`, `LANGFUSE_HOST`,
`BAO_ADDR`. `make down` now takes both profiles down.

**What each core service is, and is not, used for today.**

| Service | Consumer in this repo | Not (yet) |
|---|---|---|
| Postgres | LangGraph `AsyncPostgresSaver` checkpoints (`checkpoints*` tables); Alembic-owned `engagements` / `evidence_artefacts` schema; the separate `langfuse` database owned by the `langfuse` role | the engagement repository — persisted results live under `data/` (§14.12.2) |
| Qdrant | `regulatory_corpus` + `obligations_index` (RegulatoryRAG), one `client_docs_<engagement>` collection per run, `__embedding_meta` stamps | — |
| MinIO | `EVIDENCE_BACKEND=minio` artefacts in `aaa-evidence` (versioned) via the `evidence-rw` service account; Langfuse event/media blobs in `langfuse` via `langfuse-rw` | — |
| Valkey | Langfuse's ingestion queue (`noeviction`, AOF) | any AAA code path — `REDIS_URL` is read into settings and unused |
| OpenBao | nothing — `server -dev`, empty KV | Stage C credential storage (production item, §14.12.4) |

## 9. Live-retrieval extras

For live regulatory retrieval and non-demo execution paths:

1. start Docker services
2. populate `.env` with the required provider keys
3. run Alembic if you want the optional Postgres schema available
4. ingest the regulatory corpus into Qdrant

```bash
docker compose up -d
python -m alembic upgrade head
python -m scripts.ingest_regulatory_corpus --dry-run -v
python -m scripts.ingest_regulatory_corpus \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

## 10. Build the API documentation

The Sphinx source lives in `docs/`:

```bash
make -C docs html      # output in docs/_build/html/index.html
```

## 11. Troubleshooting quick hits

| Problem | Recommended first step |
|--------|-------------------------|
| `python3.12` missing | install Python 3.12 |
| `ModuleNotFoundError` | reactivate `.venv` |
| API imports fail | run `source .venv/bin/activate` and retry |
| `make start` does nothing visible | check `.env` — `AAA_LAUNCH_API`/`_UI` may be `false` |
| No PDF returned | inspect `/api/v1/engagements/{id}/report`; JSON output may still be available |
| Missing live retrieval | confirm Docker is running and corpus ingestion completed |
| Need to inspect persisted outputs | look under `data/results/<engagement_id>/` or use `/api/v1/data/...` |

For the end-user walkthrough, see [`USER_MANUAL.md`](./USER_MANUAL.md).
