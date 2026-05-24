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
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Authoritative multi-agent design (§1–§13) and dependency manifest (§14). |
| [`USER_MANUAL.md`](./USER_MANUAL.md) | Deep-dive into technologies and directory walkthroughs. |

---

## 1. Repository Layout

```
UAGF_TAM/
├── ARCHITECTURE.md                      # Authoritative multi-agent design
├── pyproject.toml                       # Package metadata
├── requirements.txt                     # Runtime dependencies (no pinning)
├── requirements-dev.txt                 # Dev/test dependencies
├── Makefile                             # One-line targets per milestone
├── .env.example                         # Environment template
├── aaa/                                 # Unified agentic auditor package
│   ├── agents/                          # Agents 1–12, LangGraph composition
│   ├── tools/                           # Deterministic MCP tool servers
│   ├── intake/                          # Three-stage intake pipeline
│   ├── api/                             # FastAPI platform
│   └── ui/                              # Streamlit demo
├── schemas/                             # Vendored S4 CGSA schemas
├── templates/                           # Audit-evidence templates (T01–T18)
└── tests/                               # Unit, contract, and e2e tests
```

---

## 2. Area Responsibilities

| Area | Owns | Reference § |
|------|------|-------------|
| **Agents** | Agents 1–12, LangGraph state machine, prompts, Verifier loop | §3, §5.1, §6, §8.2 |
| **Tools** | MCP servers for SHAP, fairness, RAGAs, schema validation, CSP solver | §4 |
| **Platform** | FastAPI, Postgres (`AuditState` + evidence), S3 Evidence Store | §5.2, §10 |
| **Intake** | Three-stage intake pipeline (Stage A/B/C) | §6 Stage 0 |
| **QA / Eval** | Per-tool unit tests, per-agent LLM-as-judge, e2e golden set | §9.1 |

---

## 3. Integration Contracts (the only things areas promise each other)

| Contract | Producer | Consumer(s) | File |
|----------|----------|-------------|------|
| `AuditState` typed dict | Platform | Agents, QA | `contracts/audit_state.py` |
| Agent messages (Dispatch / Report / Critique) | Agents | Platform (for persistence) | `contracts/messages.py` |
| MCP tool envelope | Tools | Agents | `contracts/mcp_tool_schema.json` |
| Evidence Store URI scheme | Platform | Agents, Tools, UI, QA | `contracts/evidence_uri.md` |
| REST surface (engagement lifecycle, CGSA ingest, HITL actions) | Platform | UI, QA | `contracts/openapi.yaml` |
| CGSA payload (from upstream S4) | external S4 | Phase 5 agent via Platform webhook | `contracts/cgsa_schema.json` |
| CGSA schema (versioned) | external S4 | Agents (Phase 5) | `schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json` |

**Rule:** any change to a file in `contracts/` requires a PR labelled `contract-change`. `contracts/CHANGELOG.md` MUST be updated in the same PR.

---

## 4. Getting Started (Bootstrap)

Full step-by-step instructions live in [`ARCHITECTURE.md`](./ARCHITECTURE.md) §14.

### 4.1 Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | **3.12** | Required for all agentic components. |
| Node.js | **≥ 20** | Required for the Next.js portal (if applicable). |
| Docker | latest | Runs Postgres, MinIO, Valkey, OpenBao, Langfuse. |

### 4.2 Installation

```bash
# 1. Clone and configure environment
git clone <repo-url> UAGF_TAM && cd UAGF_TAM
cp .env.example .env

# 2. Start the infrastructure
docker compose up -d

# 3. Setup Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install

# 4. Initialise and run
python -m alembic upgrade head
python -m pytest tests/unit
```

### 4.3 Running the Services

| Component | Command |
|-----------|---------|
| FastAPI Platform | `uvicorn aaa.api.main:app --reload` |
| Streamlit Demo | `streamlit run aaa/ui/app.py` |
| Infrastructure | `docker compose up -d` |

### 4.4 Verification

```bash
python -m pytest tests/unit
python -m aaa.cli run --case german_credit --offline
```

---

## 5. Branch & PR Rules

- **Trunk-based**, one long-lived branch: `main`.
- Every PR must pass the `ci.yml` workflow (ruff, mypy, pytest).
- No code may violate the architectural boundaries defined in `ARCHITECTURE.md`.

---

## 6. Definition of Done for the S5 Thesis

The thesis is considered tech-complete when, on the 50-engagement golden set:

- End-to-end PASS/FAIL/PASS_W_OBS verdicts agree with the human expert label on **≥ 90%** of engagements.
- Median engagement cost stays under the configured per-tier budget.
- Every report PDF carries a verifiable SHA-256 chain back to its evidence artefacts.
- The S4 → S5 webhook successfully ingests a CGSA payload and the Phase 5 agent's verdict matches `aaa_phase5_handoff.phase5_verdict` for **100%** of valid payloads.
