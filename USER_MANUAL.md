# AAA — Developer User Manual

This manual is the practical companion to:

- [`README.md`](./README.md) — quick orientation
- [`SETUP.md`](./SETUP.md) — plain-English first-run guide
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — system design and contracts
- [`PROMPT.md`](./PROMPT.md) — canonical prompt specification

---

## 1. Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | **3.12** | required |
| git | any | required |
| Docker | recent | optional; useful for online/local services |

For most development and testing, use:

```bash
export AAA_OFFLINE_MODE=true
```

That keeps the repo runnable without live LLM/API dependencies.

---

## 2. One-shot setup

```bash
git clone <repo-url> UAGF_TAM_AAA
cd UAGF_TAM_AAA
python3.12 scripts/setup.py
```

Useful flags:

```bash
python3.12 scripts/setup.py --no-docker --no-migrate
python3.12 scripts/setup.py --no-tests
python3.12 scripts/setup.py --with-prod-deps
```

Then activate the venv:

```bash
source .venv/bin/activate
```

---

## 3. Manual setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
cp .env.example .env
AAA_OFFLINE_MODE=true pytest -m "not e2e"
```

Optional local services:

```bash
docker compose up -d
python -m alembic upgrade head
```

---

## 4. Repository tour

```text
aaa/
├── agents/
│   ├── intake_validator.py          # Stage 0 A/B/C validation + T01a/T01b/T01c
│   ├── tier1/                       # Orchestrator, Verifier, RegulatoryRAG
│   ├── tier2/                       # Scope/Data/Model/Output/Governance/ReportArchitect
│   └── tier3/                       # UAGF-TAM-L, Cyber, Privacy
├── api/main.py                      # FastAPI upload-to-report flow
├── cli.py                           # offline/fixture-driven runner
├── platform/
│   ├── evidence.py                  # EvidenceStore + store_file()
│   ├── prompt_registry.py           # loads prompts from PROMPT.md
│   └── state.py                     # AuditState, Finding, RemediationItem
├── tools/
│   ├── client_doc_ingest.py         # client_doc_ingest/client_doc_search
│   ├── regulatory_coverage.py
│   ├── report_render.py
│   ├── risk_heatmap_render.py
│   └── maturity_radar_render.py
└── ui/app.py                        # Streamlit demo UI
```

Other important paths:

- `templates/` — T01a–T18 schema files
- `scripts/fixtures/uci_german_credit/` — sample intake bundle
- `scripts/fixtures/cgsa/` — offline CGSA payloads
- `tests/unit/` — focused regressions for recent thesis tasks

---

## 5. Running the system

All commands assume the venv is active.

### 5.1 CLI

```bash
python -m aaa.cli run \
  --engagement-id eng-uci-german-credit-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

Useful options:

- `--output-file out/<name>.json`
- `--annex-iv-schema-version 1.0.0`
- `--log-level INFO`

Expected output includes:

- `final_verdict`
- `art43_decision`
- KPI summary
- phase artefact URIs
- compliance matrix

### 5.2 FastAPI

```bash
uvicorn aaa.api.main:app --reload --port 8000
```

Core utility endpoints:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/api/v1/schema-version
curl http://localhost:8000/api/v1/engagements
```

### 5.3 FastAPI customer workflow example

Create engagement:

```bash
curl -X POST http://localhost:8000/api/v1/engagements \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_id": "eng-api-demo",
    "provider_name": "Demo Provider",
    "system_name": "Demo System",
    "declared_risk_tier": "high"
  }'
```

Upload a file:

```bash
curl -X POST http://localhost:8000/api/v1/engagements/eng-api-demo/files \
  -F role=risk_management_file_uri \
  -F file=@./some-risk-doc.txt
```

Submit intake:

```bash
curl -X POST http://localhost:8000/api/v1/engagements/eng-api-demo/intake \
  -H "Content-Type: application/json" \
  -d @/tmp/intake.json
```

> Build `/tmp/intake.json` by combining valid Stage A / Stage B / optional Stage C payloads, then replace Stage B file-URI fields with the values returned by the `/files` endpoint.

Run:

```bash
curl -X POST http://localhost:8000/api/v1/engagements/eng-api-demo/run
```

Fetch report metadata / PDF:

```bash
curl http://localhost:8000/api/v1/engagements/eng-api-demo/report
curl http://localhost:8000/api/v1/engagements/eng-api-demo/report.pdf --output report.pdf
```

> Note: the intake payload must contain valid Stage A/B/C structures. In practice, copy the fixture JSON and replace file URI fields with values returned by `/files`.

### 5.4 Streamlit

```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

The UI currently provides:

- Stage A editing
- Stage B required text areas
- Stage B uploaders for risk docs, post-market docs, LLM artefacts, and optional model/data artefacts
- live intake completeness preview
- final verdict display
- PDF/T18/T17 downloads
- AuditState JSON behind an advanced debug expander

---

## 6. Working with tests

### Test buckets

| Bucket | Path |
|--------|------|
| Unit | `tests/unit/` |
| Contract | `tests/contract/` |
| Golden | `tests/golden/` |
| E2E | `tests/e2e/` |

### Common commands

```bash
pytest
pytest tests/unit/ -q
pytest -m "not e2e" --cov=aaa --cov-fail-under=80
```

### High-signal regression commands for the current feature set

```bash
python -m pytest tests/unit/test_prompt_registry.py -q
python -m pytest tests/unit/test_client_doc_ingest.py -q
python -m pytest tests/unit/test_regulatory_standards_ingest.py -q
python -m pytest tests/unit/test_materiality_state.py -q
python -m pytest tests/unit/test_remediation_assignment.py -q
python -m pytest tests/unit/test_report_architect_management_response.py -q
python -m pytest tests/unit/test_risk_heatmap_render.py -q
python -m pytest tests/unit/test_maturity_radar_render.py -q
python -m pytest tests/unit/test_auditor_opinion.py -q
python -m pytest tests/unit/test_regulatory_coverage_expanded.py -q
python -m pytest tests/unit/test_evidence_store_file_upload.py -q
python -m pytest tests/unit/test_ui_upload_helpers.py -q
python -m pytest tests/unit/test_api_customer_workflow.py -q
```

---

## 7. Configuration and environment

Configuration is read from environment variables / `.env` via `aaa/settings.py`.

Most relevant settings:

| Variable | Purpose |
|----------|---------|
| `AAA_OFFLINE_MODE` | disables external LLM/API reliance for local/dev use |
| `AAA_LOG_LEVEL` | logging level |
| `CGSA_FIXTURE_DIR` | offline CGSA source |
| `S4_CGSA_BASE_URL` | live S4 URL |
| `QDRANT_URL` | vector store URL |
| `OPENAI_API_KEY` | online embeddings / model calls |

### Prompt runtime

Prompts are now sourced from:

- `PROMPT.md` — human-readable source of truth
- `aaa/platform/prompt_registry.py` — runtime loader / version hash

If you update prompt wording, update the source in `PROMPT.md` and then run the prompt tests.

---

## 8. Common developer workflows

### 8.1 Update prompts

1. Edit `PROMPT.md`
2. Verify the affected prompt loads via `aaa/platform/prompt_registry.py`
3. Run:

```bash
pytest tests/unit/test_prompt_registry.py -q
pytest tests/unit/test_prompt_snapshots.py -q
```

### 8.2 Work on client-document RAG

Relevant files:

- `aaa/tools/client_doc_ingest.py`
- `aaa/agents/intake_validator.py`
- phase agents that call `client_doc_search`

Key behavior:

- uploaded documents are ingested into `client_docs_{engagement_id}`
- embeddings use `text-embedding-3-large`
- offline mode returns safe no-op / empty results

### 8.3 Add or change a report field

Usually touches:

- `aaa/platform/state.py`
- `templates/T18_audit_report.json`
- `aaa/agents/tier2/report_architect.py`
- `aaa/tools/report_render.py`
- corresponding unit tests

### 8.4 Add a new template

1. add schema in `templates/`
2. mirror packaged copy in `packages/uagf_tam_templates/`
3. wire the template into the owning agent
4. add tests

### 8.5 Inspect generated outputs

```bash
python -m aaa.cli run \
  --engagement-id eng-uci-german-credit-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --output-file out/eng-uci-german-credit-001.json \
  --offline
```

Then inspect:

- `out/eng-uci-german-credit-001.json`
- `phase_artefacts.T17_compliance_matrix`
- `phase_artefacts.T18_audit_report`

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: aaa` | wrong cwd or inactive venv | activate `.venv`, run from repo root |
| `python3.12: command not found` | Python missing | install Python 3.12 |
| Streamlit import errors | dev deps missing | `pip install -r requirements-dev.txt` |
| `OPENAI_API_KEY not set` during corpus ingest | missing `.env` / key | add key or use offline mode |
| `report.pdf` returns 404 | PDF renderer unavailable for that run | use `/report` JSON metadata; JSON report is always produced |
| client doc search returns empty results | offline mode or collection absent | disable offline mode and ingest docs, or confirm uploads reached IntakeValidator |
| ingestion appears to hang on macOS | native library verification | wait 10–30 seconds on first run |
| ISO PDF loads zero units | wrong PDF backend | ensure `pypdfium2>=5.8.0` is installed |

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| AAA | Autonomous AI Auditor |
| AuditState | shared engagement state threaded through the graph |
| EvidenceStore | artefact storage abstraction; supports `store_artefact()` and `store_file()` |
| IntakeValidator | Stage 0 validator for T01a/T01b/T01c and document ingestion |
| ReportArchitect | Phase 6 agent that assembles T17/T18 and rendered report outputs |
| T17 | final compliance matrix |
| T18 | final audit report |
| HITL | human-in-the-loop escalation |
| L-branch | LLM / agentic execution path |
| CGSA | governance payload consumed in Phase 5 |
