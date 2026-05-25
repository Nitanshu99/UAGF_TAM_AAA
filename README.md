# AAA — Autonomous AI Auditor (S5 Thesis)

End-to-end implementation of the 12-agent system specified in [`ARCHITECTURE.md`](./ARCHITECTURE.md). The system consumes the upstream S4 `uagf_cgsa_aaa_schema.json` payload at Phase 5 and emits an Annex IV–aligned EU AI Act conformity-assessment report at Phase 6.

> **Single source of truth:** [`ARCHITECTURE.md`](./ARCHITECTURE.md). Every design decision must be traceable to a section of that document.

> **Python 3.12 is REQUIRED**. The system relies on `uvicorn`, `streamlit`, and `pytest` for its runtime and verification.

> **Open-source-first stack** (`ARCHITECTURE.md` §1 principle 6). Every infrastructure component is OSI-approved or Linux-Foundation-stewarded:
> LangGraph · LangChain · LiteLLM · PostgreSQL · pgvector · MinIO · Valkey · OpenBao · OpenTofu · Helm · Langfuse · Grafana · Loki · Prometheus · OpenTelemetry · Keycloak · Next.js · FastAPI.
> The only externally-hosted dependencies are **LLM provider APIs** — Anthropic Claude, OpenAI GPT, DeepSeek, Mistral, or a local Ollama runtime — all interchangeable through LiteLLM. **No proprietary SaaS** (no Vercel, no HashiCorp Vault, no LangSmith, no Terraform, no managed Redis).

### Documentation Map

| File | Purpose |
|------|---------|
| [`README.md`](./README.md) | This file — high-level orientation, repo layout, bootstrap quick-start. |
| [`USER_MANUAL.md`](./USER_MANUAL.md) | Step-by-step developer guide: install, run the CLI/API/UI, write tests, troubleshoot. |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Authoritative multi-agent design (§1–§13) and dependency manifest (§14). |
| [`tasks.md`](./tasks.md) | Per-group implementation log (Groups 1–11). |
| [`infra/runbook.md`](./infra/runbook.md) | On-call runbook mirroring `ARCHITECTURE.md` §14.9. |

---

## 1. Repository Layout

```
UAGF_TAM_AAA/
├── ARCHITECTURE.md                # Authoritative multi-agent design
├── README.md                      # This file
├── USER_MANUAL.md                 # Developer guide
├── tasks.md                       # Per-group implementation log
├── Makefile                       # One-line targets per milestone
├── pyproject.toml                 # Package metadata + pytest config
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Dev/test dependencies (extends runtime)
├── .env.example                   # Environment template
├── docker-compose.yml             # Local dev stack (Postgres/MinIO/...)
├── docker-compose.prod.yml        # Production stack
├── alembic.ini, alembic/          # Database migrations
├── aaa/                           # Unified agentic auditor package
│   ├── agents/                    # Tier 1/2/3 agents + IntakeValidator
│   ├── tools/                     # ~30 deterministic MCP tools
│   ├── platform/                  # AuditState, EvidenceStore
│   ├── api/main.py                # FastAPI app (engagement CRUD + health)
│   ├── ui/app.py                  # Streamlit demo
│   ├── cli.py                     # `python -m aaa.cli run ...`
│   └── settings.py                # pydantic-settings config singleton
├── schemas/cgsa/v1.0.0/           # Vendored S4 CGSA schemas
├── templates/                     # Audit-evidence templates (T01a–T18)
├── packages/uagf_tam_templates/   # Distributable template package (PyPI-ready)
├── scripts/
│   ├── setup.py                   # One-shot environment bootstrap
│   └── fixtures/                  # Reference engagement payloads
├── infra/tofu/                    # OpenTofu IaC stub
├── infra/runbook.md               # On-call runbook
├── .github/workflows/             # CI, schema-drift, release pipelines
└── tests/                         # unit / contract / golden / e2e
```

---

## 2. Area Responsibilities

| Area | Owns | Reference § |
|------|------|-------------|
| **Agents** | Agents 1–12, LangGraph state machine, prompts, Verifier loop | §3, §5.1, §6, §8.2 |
| **Tools** | MCP servers for SHAP, fairness, RAGAs, schema validation, CSP solver | §4 |
| **Platform** | FastAPI, Postgres (`AuditState` + evidence), S3 Evidence Store | §5.2, §10 |
| **Intake** | Three-stage intake pipeline (Stage A/B/C) inside `aaa/agents/intake_validator.py` | §6 Stage 0 |
| **QA / Eval** | Unit / contract / golden / e2e suites under `tests/` | §9.1 |

---

## 3. Integration Contracts (the only things areas promise each other)

| Contract | Producer | Consumer(s) | File |
|----------|----------|-------------|------|
| `AuditState` typed dict | Platform | Agents, QA | `aaa/platform/state.py` |
| Agent messages (Dispatch / Report / Critique) | Agents | Platform | `aaa/agents/base.py` |
| Evidence Store URI scheme | Platform | Agents, Tools, UI | `aaa/platform/evidence.py` |
| REST surface (engagement lifecycle, healthz) | Platform | UI, QA | `aaa/api/main.py` |
| CGSA payload (from upstream S4) | external S4 | Phase 5 agent | `schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json` |
| CGSA schema-version drift gate | CI | Engineering | `.github/workflows/s4_contract.yml` |

**Rule:** any change to `aaa/platform/state.py` or `schemas/cgsa/**` requires the schema-drift gate to be acknowledged in the PR.

---

## 4. Getting Started (Bootstrap)

### 4.1 One-shot setup (recommended)

```bash
git clone <repo-url> UAGF_TAM_AAA && cd UAGF_TAM_AAA
python3.12 scripts/setup.py            # creates venv, installs deps, copies .env, runs smoke test
```

`scripts/setup.py` is idempotent — re-running it will only redo the steps that are missing.
Flags: `--no-docker` (skip docker compose up), `--no-migrate` (skip alembic), `--with-prod-deps` (install full runtime requirements).

### 4.2 Manual setup

| Step | Command |
|------|---------|
| Create venv | `python3.12 -m venv .venv && source .venv/bin/activate` |
| Install dev deps | `pip install -r requirements-dev.txt` |
| Copy env file | `cp .env.example .env` |
| Start infra (optional) | `docker compose up -d` |
| Run migrations (optional) | `python -m alembic upgrade head` |
| Run tests | `pytest -m "not e2e"` |

Full walkthrough in [`USER_MANUAL.md`](./USER_MANUAL.md).

### 4.3 Running the Services

| Component | Command |
|-----------|---------|
| FastAPI Platform | `uvicorn aaa.api.main:app --reload` |
| Streamlit Demo | `AAA_OFFLINE_MODE=true streamlit run aaa/ui/app.py` |
| CLI (offline demo) | `python -m aaa.cli run --engagement-id eng-demo-001 --intake-dir scripts/fixtures/uci_german_credit --cgsa-fixture-dir scripts/fixtures/cgsa --offline` |
| Infrastructure | `docker compose up -d` |

### 4.4 Verification

```bash
pytest -m "not e2e" --cov=aaa --cov-fail-under=80     # full unit+contract+golden suite
make intake-demo                                       # offline end-to-end on UCI German Credit
```

---

## 5. Branch & PR Rules

- **Trunk-based**, one long-lived branch: `main`.
- Every PR must pass the `ci.yml` workflow (ruff, mypy, pytest, coverage ≥ 80 %).
- No code may violate the architectural boundaries defined in `ARCHITECTURE.md`.

---

## 5a. Recent Improvements — Regulatory Corpus Ingestion

The following improvements were made to `scripts/ingest_regulatory_corpus.py` and the supporting infrastructure after the initial implementation. All changes are backward-compatible.

| Improvement | Detail |
|---|---|
| **ISO/IEC 42001 ingestion** | Switched PDF backend from `pdfplumber` (returned 0 pages) to `pypdfium2`, which correctly reads ISO's newline-separated object-token layout. `pypdfium2>=5.8.0` is now listed in `requirements.txt`. |
| **Split-line clause/control headings** | ISO 42001 often places a clause or control number (e.g. `A.10.3`) on its own line with the title on the next line. Three new regexes (`_ISO_CLAUSE_NUM_RE`, `_ISO_CONTROL_NUM_RE`, `_ISO_TITLE_HEAD_RE`) handle this correctly so all 32 clauses and 56 Annex A controls are captured. |
| **Warning on empty loader** | `load_pdf_units()` and `_load_all_units()` now emit an explicit `_warn(...)` message when a source file produces zero units, preventing silent failures. |
| **Idempotent ingestion (skip-existing)** | Each chunk point ID is a deterministic SHA-256 of `text + regulation + ref + chunk_index`. On re-run, `_fetch_existing_ids()` scrolls the Qdrant collection and skips any chunks already present — zero extra OpenAI API calls. |
| **Automatic `.env` loading** | The script calls `load_dotenv()` at startup via `python-dotenv`. No `source .env` shell step is required before running the script. |
| **Import warm-up (macOS Gatekeeper)** | `numpy`, `sklearn`, `nltk`, and `qdrant_client` are imported early in `main()` so macOS Gatekeeper verifies the native `.so` extensions at the start rather than mid-run (which previously caused `SIGINT` / hanging). |

### Corpus state after full ingestion

| Regulation | Chunks in `regulatory_corpus` |
|---|---|
| EU AI Act | **339** (136 articles + 181 recitals + 22 annexes) |
| GDPR | **288** (115 articles + 173 recitals) |
| ISO/IEC 42001 | **88** (32 clauses §4–§10 + 56 Annex A controls) |
| **Total** | **715** |

`obligations_index` contains **15** obligation-question points derived from the compliance-checker JSON.

---

## 6. Definition of Done for the S5 Thesis

The thesis is considered tech-complete when, on the 50-engagement golden set:

- End-to-end PASS/FAIL/PASS_W_OBS verdicts agree with the human expert label on **≥ 90 %** of engagements.
- Median engagement cost stays under the configured per-tier budget.
- Every report PDF carries a verifiable SHA-256 chain back to its evidence artefacts.
- The S4 → S5 webhook successfully ingests a CGSA payload and the Phase 5 agent's verdict matches `aaa_phase5_handoff.phase5_verdict` for **100 %** of valid payloads.
