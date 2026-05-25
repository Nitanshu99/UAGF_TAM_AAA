# AAA — Developer User Manual

> Step-by-step guide for a **new contributor** to clone, run, test, and extend the
> Autonomous AI Auditor (AAA). Pair this manual with:
>
> - [`README.md`](./README.md) — repo orientation
> - [`ARCHITECTURE.md`](./ARCHITECTURE.md) — authoritative design (§1–§14)
> - [`infra/runbook.md`](./infra/runbook.md) — production on-call procedures

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [One-shot setup](#2-one-shot-setup)
3. [Manual setup (what the script does)](#3-manual-setup-what-the-script-does)
4. [Repository tour](#4-repository-tour)
5. [Running the system](#5-running-the-system)
6. [Working with tests](#6-working-with-tests)
7. [Configuration & environment variables](#7-configuration--environment-variables)
8. [Common developer workflows](#8-common-developer-workflows)
9. [Troubleshooting](#9-troubleshooting)
10. [Glossary](#10-glossary)

---

## 1. Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| **Python** | **3.12** (exact) | `pyproject.toml`, type hints, asyncio idioms |
| **git** | any | clone the repo |
| **Docker Desktop** | latest | local Postgres / MinIO / Valkey / Langfuse stack (optional in offline mode) |
| **GNU Make** | any | one-line `make <target>` shortcuts (optional) |

> **Offline mode.** Every component is designed to run with `AAA_OFFLINE_MODE=true`,
> which means **no network, no LLM API key, no Docker is strictly required** to
> develop or run the test suite. Set this flag whenever you don't need real LLMs.

Check your Python version:

```bash
python3.12 --version          # must print "Python 3.12.x"
```

If `python3.12` is not on your PATH, install it via [pyenv](https://github.com/pyenv/pyenv), `brew install python@3.12`, or your distro's package manager.

---

## 2. One-shot setup

The repository ships with [`scripts/setup.py`](./scripts/setup.py) — a single
idempotent Python script that bootstraps everything:

```bash
git clone <repo-url> UAGF_TAM_AAA
cd UAGF_TAM_AAA
python3.12 scripts/setup.py
```

What this does (each step is skipped if already done):

| Step | Action |
|------|--------|
| 1 | Verify Python ≥ 3.12 |
| 2 | Create `.venv/` |
| 3 | Upgrade pip; install `requirements-dev.txt` |
| 4 | Copy `.env.example` → `.env` (if missing) |
| 5 | Start `docker compose` stack (skipped if Docker is missing) |
| 6 | Apply Alembic migrations (warns and continues on failure) |
| 7 | Run the offline pytest smoke suite (`-m "not e2e"`) |

Useful flags:

```bash
python3.12 scripts/setup.py --no-docker --no-migrate    # purely Python install
python3.12 scripts/setup.py --no-tests                   # skip smoke run
python3.12 scripts/setup.py --with-prod-deps             # heavy ML stack (SHAP, torch, ...)
```

Re-run it any time — completed steps will report "already present" and skip.

---

## 3. Manual setup (what the script does)

If you prefer running each step yourself:

```bash
# 3.1 — Virtualenv
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3.2 — Dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
# (optional) full ML stack — only needed for Tier-2/3 tools that import shap, torch, ...
pip install -r requirements.txt

# 3.3 — Environment file
cp .env.example .env
# Edit .env — fill in LLM API keys ONLY if you intend to run online.

# 3.4 — (optional) Local services
docker compose up -d
python -m alembic upgrade head

# 3.5 — Smoke test
AAA_OFFLINE_MODE=true pytest -m "not e2e"
```

---

## 4. Repository tour

```
UAGF_TAM_AAA/
├── aaa/                            # main Python package
│   ├── agents/
│   │   ├── intake_validator.py     # Stage 0 A/B/C dispatch
│   │   ├── tier1/                  # Orchestrator, Verifier, RegulatoryRAG
│   │   ├── tier2/                  # ScopeAgent, DataAuditor, ModelValidator,
│   │   │                           # OutputFairness, GovernanceAgent, ReportArchitect
│   │   └── tier3/                  # UagfTamLBranch, CyberAgent, PrivacyAgent
│   ├── tools/                      # ~30 deterministic MCP tools (SHAP, LIME, RAGAs, ...)
│   ├── platform/
│   │   ├── state.py                # AuditState TypedDict — the system's contract
│   │   └── evidence.py             # EvidenceStore (in-memory; swappable for MinIO)
│   ├── api/main.py                 # FastAPI app
│   ├── ui/app.py                   # Streamlit demo
│   ├── cli.py                      # CLI entrypoint
│   └── settings.py                 # pydantic-settings singleton
│
├── schemas/cgsa/v1.0.0/            # Canonical S4 CGSA JSON schema (vendored)
├── templates/T01a_*.json ... T18_*.json
│                                   # Audit-evidence template schemas
├── packages/uagf_tam_templates/    # PyPI-ready template loader package
│
├── scripts/
│   ├── setup.py                    # one-shot bootstrap (see §2)
│   └── fixtures/                   # reference engagement payloads
│       ├── uci_german_credit/      #   stage_a.json + stage_b.json + stage_c.json
│       └── cgsa/                   #   CGSA payloads used in offline mode
│
├── tests/
│   ├── unit/                       # pure function tests (no network, no Docker)
│   ├── contract/                   # CGSA fixture schema-conformance tests
│   ├── golden/                     # regression tests against out/ reference JSON
│   └── e2e/                        # full-stack tests (skipped offline)
│
├── alembic/                        # DB migrations
├── docker-compose.yml              # local dev stack
├── infra/tofu/                     # OpenTofu IaC stub (production)
└── .github/workflows/              # CI / schema-drift / release pipelines
```

---

## 5. Running the system

All commands below assume your venv is active (`source .venv/bin/activate`).

### 5.1 CLI — run a full audit (offline)

```bash
python -m aaa.cli run \
  --engagement-id eng-demo-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

Equivalent Makefile target:

```bash
make intake-demo
```

What you get on stdout: a JSON summary with `final_verdict`, `intake_completeness_score`,
`completeness_score`, `regulatory_coverage_pct`, `art43_decision`, the `phase_artefacts`
URI map, and the compliance matrix. Exit code `0` = success, `2` = intake gate failure,
`3` = pipeline error.

### 5.2 FastAPI — engagement CRUD + health

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Then in another terminal:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/api/v1/schema-version
curl -X POST http://localhost:8000/api/v1/engagements \
     -H "Content-Type: application/json" \
     -d '{"provider_name":"Acme","system_name":"CreditAI","declared_risk_tier":"high"}'
```

OpenAPI / Swagger UI is auto-served at `http://localhost:8000/docs`.

### 5.3 Streamlit demo

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

Opens a browser at `http://localhost:8501` with the Stage A/B/C wizard, live
intake-completeness preview, and a "Run full audit" button that triggers the
same pipeline as the CLI.

### 5.4 Make targets cheat-sheet

| Target | Effect |
|--------|--------|
| `make install` | venv + dev deps + pre-commit |
| `make up` / `make down` | docker compose up/down + alembic upgrade |
| `make lint` | ruff + mypy |
| `make test` | full pytest (offline-friendly) |
| `make coverage` | pytest with `--cov-fail-under=80` |
| `make intake-validate` | run only the IntakeValidator (Stage 0) on the fixture |
| `make intake-demo` | full offline pipeline on UCI German Credit |
| `make m3-linear` / `m4-full` | exposé milestones M3 / M4 |
| `make demo` | Streamlit demo in offline mode |

---

## 6. Working with tests

The test suite is organised into four buckets:

| Bucket | Path | Marker | Runs in CI? |
|--------|------|--------|-------------|
| Unit | `tests/unit/` | (none) | ✅ |
| Contract | `tests/contract/` | `@pytest.mark.contract` | ✅ |
| Golden | `tests/golden/` | `@pytest.mark.golden` | ✅ |
| End-to-end | `tests/e2e/` | `@pytest.mark.e2e` | ❌ (skipped offline) |

### Run them

```bash
pytest                                       # everything (e2e auto-skipped offline)
pytest tests/unit/ -v                        # one bucket
pytest -m "contract"                         # by marker
pytest -m "not e2e" --cov=aaa --cov-fail-under=80
pytest tests/unit/test_cgsa_ingest.py::test_cgsa_ingest_happy_path  # single test
```

### Coverage gate

CI runs `pytest --cov=aaa --cov-fail-under=80`. A PR that drops coverage below
80 % fails the `ci.yml` workflow.

### Adding a new test

- **Unit**: drop a file under `tests/unit/`. No new file naming rules beyond
  `test_*.py`.
- **Contract**: if you add a new CGSA fixture under `scripts/fixtures/cgsa/`,
  the parametrised tests in `tests/contract/test_cgsa_fixture_contract.py`
  pick it up automatically.
- **Golden**: regenerate the reference JSON in `out/` with
  `make m4-full --output-file out/<id>.json`, then add assertions in
  `tests/golden/test_golden_output.py`.
- **E2E**: add to `tests/e2e/test_e2e_placeholder.py` and gate with
  `@pytest.mark.e2e`. Will only run when `AAA_OFFLINE_MODE` is unset.

---

## 7. Configuration & environment variables

All configuration is read from environment variables or a `.env` file at the
repo root (see [`.env.example`](./.env.example) for the full annotated list).
The pydantic-settings singleton lives at [`aaa/settings.py`](./aaa/settings.py).

> **Ingestion script loads `.env` automatically.** `scripts/ingest_regulatory_corpus.py` calls `load_dotenv()` at startup via `python-dotenv`, so you can run it directly without `source .env`.

Use it from code:

```python
from aaa.settings import settings

if settings.is_offline():
    # don't make HTTP / LLM calls
    ...
```

The most important flags for day-to-day development:

| Variable | Default | Purpose |
|----------|---------|---------|
| `AAA_OFFLINE_MODE` | `false` | Set `true` to disable all HTTP / LLM calls — required for CI and the Streamlit demo. |
| `AAA_LOG_LEVEL` | `WARNING` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `CGSA_FIXTURE_DIR` | `scripts/fixtures/cgsa` | Where the offline CGSA payloads live. |
| `S4_CGSA_BASE_URL` | `http://localhost:8001` | Upstream S4 FastAPI URL (online mode). |
| `DATABASE_URL` | `postgresql://aaa:changeme@localhost:5432/aaa` | Postgres connection string for Alembic + Platform. |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | — | Only needed when **not** in offline mode. |

> **Never commit `.env`**. The file is in `.gitignore`. Use the `OpenBao`
> instance (started by `docker compose`) for real secrets in production.

---

## 8. Common developer workflows

### 8.1 "I want to add a new MCP tool"

1. Create `aaa/tools/my_tool.py` exporting a single pure function.
2. Add a unit test under `tests/unit/test_my_tool.py`.
3. Wire it into the agent that needs it (most agents live under `aaa/agents/tierN/`).
4. Run `pytest tests/unit/test_my_tool.py -v` until green.
5. Run `pytest --cov=aaa --cov-fail-under=80` to confirm the gate still holds.

### 8.2 "I want to add a new audit-evidence template"

1. Drop a JSON Schema at `templates/T<NN>_<name>.json` (draft-07).
2. Mirror it into the packaged copy at
   `packages/uagf_tam_templates/src/uagf_tam_templates/schemas/T<NN>_<name>.json`.
3. Add a contract assertion in `packages/uagf_tam_templates/tests/test_loader.py`.
4. Reference the new T-ID from the appropriate agent (`ReportArchitect` for T17/T18,
   tier-2 agents for T02–T15, tier-3 agents for T16).

### 8.3 "I want to change a CGSA schema field"

The CGSA schema is the contract with the upstream **S4** system. Changing it
will trip the nightly `s4_contract.yml` GitHub Action.

1. Update `schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json`.
2. Bump the version directory if it is a breaking change (e.g. `v1.1.0/`)
   and update `CGSA_SCHEMA_VERSION` in `.env.example` and `aaa/settings.py`.
3. Regenerate every fixture under `scripts/fixtures/cgsa/`.
4. Re-run `pytest tests/contract/ -v` until all fixtures pass.
5. Coordinate the change with the S4 owners (see [`infra/runbook.md`](./infra/runbook.md)
   "Schema drift" row).

### 8.4 "I want to run only Stage 0 (Intake) on a fixture"

```bash
make intake-validate
# equivalent to:
python -m aaa.cli run \
    --engagement-id eng-validate-001 \
    --intake-dir scripts/fixtures/uci_german_credit \
    --offline
```

### 8.5 "I want to inspect what the orchestrator produced"

The full audit summary is written to `out/eng-<id>.json` when you pass
`--output-file`. The golden test suite (`tests/golden/`) reads from
`out/eng-uci-german-credit-001.json` as the reference.

```bash
python -m aaa.cli run \
    --engagement-id eng-uci-german-credit-001 \
    --intake-dir scripts/fixtures/uci_german_credit \
    --cgsa-fixture-dir scripts/fixtures/cgsa \
    --output-file out/eng-uci-german-credit-001.json \
    --offline
jq '.phase_artefacts | keys' out/eng-uci-german-credit-001.json
```

### 8.6 "I want to publish a PR"

1. Branch from `main`: `git switch -c feat/<topic>`.
2. Make changes, add/update tests.
3. `make lint && make coverage` locally — both must pass.
4. Push and open a PR. The `ci.yml` workflow will repeat lint + coverage.
5. If you touched `schemas/cgsa/**`, label the PR `contract-change`.

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: aaa` | venv not active, or repo root not on PATH | `source .venv/bin/activate`; run from repo root |
| `python3.12: command not found` | Python 3.12 not installed | `brew install python@3.12` (macOS) or `pyenv install 3.12` |
| Tests fail with `CGSAIngestError: schema_validation_failed` | hand-crafted payload missing required field | use `scripts/fixtures/cgsa/uci-german-credit-001.json` as the base, mutate copies |
| `streamlit run aaa/ui/app.py` shows `ModuleNotFoundError: streamlit` | dev deps not installed | `pip install -r requirements-dev.txt` |
| `docker compose up` hangs on Postgres `pg_isready` | port 5432 already in use locally | `lsof -i :5432` to find the conflict; stop the other postgres or change the port in `docker-compose.yml` |
| `alembic upgrade head` → `connection refused` | Postgres container not up | `docker compose up -d postgres` first, wait 5 s, retry |
| pytest skips all e2e tests | `AAA_OFFLINE_MODE=true` (the default in CI) | unset the variable, **and** make sure `docker compose` is up before running e2e |
| Coverage gate fails at 79.x % | recent code without tests | add unit tests; rerun `pytest --cov=aaa --cov-report=term-missing` to see which lines are uncovered |
| `make` target fails with "command not found: .venv/bin/python" | venv not created yet | run `python3.12 scripts/setup.py` once |
| LLM call raises `401 Unauthorized` | API key missing or wrong | check `.env`; or set `AAA_OFFLINE_MODE=true` to bypass LLM calls entirely |
| Ingestion script appears to hang (no output) on macOS | macOS Gatekeeper is verifying native `.so` extensions (qdrant_client, sklearn, nltk) on first use | Wait 10–30 s; the script pre-warms these imports at startup so the delay is front-loaded and only occurs once per new install |
| `loaded 0 units from ISO:IEC 42001-2023.pdf` | Old `pdfplumber` backend silently returns 0 pages for ISO's token layout | Ensure `pypdfium2>=5.8.0` is installed (`pip show pypdfium2`); the script now uses it automatically |
| Re-running ingestion embeds all chunks again and incurs OpenAI costs | Point IDs changed (e.g. chunking parameters were changed) | Run `--reset` to drop and rebuild collections, **or** keep chunking params constant — idempotent skip-existing logic uses SHA-256 IDs |
| Script exits with `OPENAI_API_KEY not set` | `.env` not present or key missing | The script loads `.env` automatically via `python-dotenv`; create or check `.env` at the repo root |

If the above does not help, capture the failing command + full traceback and
open an issue. The runbook ([`infra/runbook.md`](./infra/runbook.md)) covers
production-class incidents.

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| **AAA** | Autonomous AI Auditor — this repository. |
| **S4** | Upstream system that emits the CGSA payload consumed at Phase 5. |
| **CGSA** | Compliance, Governance, Security & Assurance — the JSON schema vendored under `schemas/cgsa/v1.0.0/`. |
| **AuditState** | The single TypedDict (`aaa/platform/state.py`) all agents read from and write to. |
| **Evidence Store** | Content-addressed artefact store; in-memory in offline mode, MinIO in production. |
| **IntakeValidator** | Stage 0 agent: ingests T01a/T01b/T01c, runs the completeness gate (≥ 0.80). |
| **Orchestrator** | LangGraph state machine running Phases 0–6 (`aaa/agents/tier1/orchestrator.py`). |
| **Tier 1 / 2 / 3** | Agent tiering by responsibility — Tier 1 = control plane, Tier 2 = phase workers, Tier 3 = on-demand specialists. |
| **T01a … T18** | Audit evidence templates — 20 JSON Schemas under `templates/`. |
| **L-branch** | LLM/agentic execution path (`is_llm_or_agentic=true`); replaces Phases 2–4 with `UagfTamLBranch`. |
| **HITL** | Human-In-The-Loop — review trigger when the system detects ambiguity. |
| **KPI 0 / 1 / 2** | Intake completeness / phase completeness / regulatory coverage (see `aaa/tools/intake_completeness_calculator.py`, `aaa/tools/completeness_score.py`, `aaa/tools/regulatory_coverage.py`). |
| **CSP** | Constraint Satisfaction Problem — solved with `python-constraint` to verify hard regulatory constraints (§6.2). |

---

*Last updated alongside the test-suite landing (42 unit/contract/golden tests passing, 4 e2e skipped offline).*
