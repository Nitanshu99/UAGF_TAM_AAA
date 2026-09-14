# AAA — Autonomous AI Auditor

AAA is a modular EU AI Act audit system built around a **14-agent pipeline**, a
FastAPI integration surface, a Streamlit wizard UI, structured observability,
and a lightweight file-based persistence layer for demo and thesis workflows.

> **Python 3.12 is required.**

## Contents

- [Quick start (autostart)](#quick-start-autostart) — clone, drop in the two bundles, run one command
- [Run the whole stack with one command](#run-the-whole-stack-with-one-command)
- [First-time bootstrap](#first-time-bootstrap)
- [Audit methodology](#audit-methodology--evidence-grounded-not-rubber-stamped)
- [Documentation](#documentation) · [Main surfaces](#main-surfaces)
- [What is persisted locally](#what-is-persisted-locally)
- [Observability and monitoring](#observability-and-monitoring)
- [REST API summary](#rest-api-summary)
- [Repository layout](#repository-layout) · [Regulatory corpus](#regulatory-corpus)

## Quick start (autostart)

Everything below is one command once the prerequisites are in place.

**You need:** Python 3.12, git, Docker Desktop (running), one OpenRouter key
(`https://openrouter.ai/keys`), and the two bundles handed over separately:
`mariposa.zip` (the Mariposa intake bundle) and `corpus.zip` (the regulatory
corpus with the compliance checker).

```bash
git clone <this repository> UAGF_TAM_AAA && cd UAGF_TAM_AAA
cp /path/to/mariposa.zip /path/to/corpus.zip .
python3.12 bootstrap.py            # asks for the OpenRouter key once (hidden input)
```

What happens, in order (every step is skipped when already done, so re-running
after a failure or a `git pull` is safe):

1. `.venv` + dependencies (about 5 minutes the first time).
2. `.env` written from `.env.example`: OpenRouter for the agent roster **and**
   for embeddings (`text-embedding-3-large` through OpenRouter), so no other
   vendor key is needed; Langfuse provisioned with generated keys and a login.
3. Bundles unpacked to `mock/06_mariposa_edu_gmbh/` and `data/`.
4. Docker: Postgres, Qdrant, MinIO, Valkey, ClickHouse, Langfuse, OpenBao,
   Prometheus, Loki, Alloy, Grafana, pgweb, redis-commander — waited on until healthy.
5. Migrations, Chromium for Playwright.
6. The regulatory corpus embedded into Qdrant (1 200 chunks; a few cents, once).
7. API + wizard started, then one Chromium window: Grafana, Loki logs, Prometheus,
   Alloy, Langfuse, Qdrant, Postgres, MinIO, Valkey and the API each in a tab
   (Grafana, Langfuse and MinIO already signed in), the wizard in front, filled
   from the bundle and dispatched.

The bootstrap audits with the **reference configuration** the published Mariposa
result was produced with — `OPENROUTER_MODEL=minimax/minimax-m3` pinned to
`OPENROUTER_PROVIDER=coreweave/fp4` (a paid endpoint; about 55 model calls and
roughly USD 0.30 per run, 15 minutes). It writes these two keys only when `.env`
leaves them blank. For the free route instead, set
`OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b` and `OPENROUTER_PROVIDER=none`
(60–90 minutes, results will differ from the reference). The results
page renders in the front tab; the window stays open afterwards. Deliverables
land under `data/customer/mariposa_edu_gmbh/`, downloads from the page under
`downloads/`, the API/UI logs under `logs/bootstrap/`.

**Stop:** `Ctrl-C` in the terminal (or `pkill -f scripts.bootstrap`) closes the
browser, API and UI; the Docker stack keeps running with its data until
`docker compose --profile obs --profile ui down`.

**Choose the model.** The free route is the default. To pin a paid endpoint set
both in `.env` before running, e.g. `OPENROUTER_MODEL=minimax/minimax-m3` and
`OPENROUTER_PROVIDER=coreweave/fp4` (see `.env.example`; the pin is what selects
the paid slug). Prices for the cost panel come from `MODEL_PRICES_USD_PER_1M`.

**Useful variants:**

```bash
python3.12 bootstrap.py --mock-llm            # same path, nothing spent: local stub, deterministic verdicts
python3.12 bootstrap.py --no-run              # fill the wizard, do not dispatch
python3.12 bootstrap.py --screenshots shots/  # PNG of every tab, the form and the results
python3.12 bootstrap.py --help
```


Everything — Docker infrastructure, database migrations, the FastAPI backend,
and the Streamlit UI — starts from a single entry point:

```bash
make start          # or:  python -m aaa   (or the `aaa` console script)
```

The launcher reads its plan from `.env`, so a fresh clone works with defaults.
The relevant knobs (all optional):

| Variable | Default | Effect |
|----------|---------|--------|
| `AAA_LAUNCH_DOCKER` | `auto` | Start the Docker Compose infra (`auto`/`true`/`false`). |
| `AAA_LAUNCH_MIGRATE` | `auto` | Run Alembic migrations on start. |
| `AAA_LAUNCH_API` | `true` | Start the FastAPI backend. |
| `AAA_LAUNCH_UI` | `true` | Start the Streamlit UI. |
| `PLATFORM_PORT` | `8000` | FastAPI port. |
| `STREAMLIT_SERVER_PORT` | `8501` | Streamlit port. |

Once it is up: Streamlit at `http://localhost:8501`, Swagger UI at
`http://localhost:8000/docs`.

To run a single surface instead of the whole stack:

```bash
aaa ui                          # Streamlit wizard only
aaa api                         # FastAPI backend only
aaa audit --engagement-id ...   # headless CLI audit of a fixture
```

## First-time bootstrap

**Zero to a running audit in one command** (the [quick start](#quick-start-autostart)
above walks through it step by step). Put the two bundles you were handed —
`mariposa.zip` (the Mariposa intake bundle) and `corpus.zip` (the regulatory
corpus) — in the repository root, then:

```bash
python3.12 bootstrap.py          # or:  make bootstrap
```

It asks for one OpenRouter key and does the rest: `.venv` and dependencies,
`.env` (OpenRouter for the agent roster *and* for embeddings — the same
`text-embedding-3-large`, reached through OpenRouter, so no OpenAI key is
needed), unpacks the bundles, starts Docker with the observability stack and
the service UIs, applies migrations, installs Chromium, embeds the corpus into
Qdrant, starts the API and the wizard, and opens one browser window: Grafana,
Loki, Prometheus, Alloy, Langfuse, Qdrant, Postgres, MinIO, Valkey and the API
each in a tab (already signed in where a login exists), and the wizard in
front — filled from the bundle and running.
The window stays open when the run ends. Every step is idempotent, so re-running
after a failure or a `git pull` only does what is still missing.

```bash
python3.12 bootstrap.py --mock-llm   # same path, no paid calls (local stub)
python3.12 bootstrap.py --no-run     # fill the wizard, do not dispatch
python3.12 bootstrap.py --help       # every option
```

The lighter, older path is still there for a laptop-only checkout:

```bash
python3.12 -m scripts.setup --no-docker --no-migrate   # venv + deps + .env
source .venv/bin/activate
```

See [SETUP.md](./SETUP.md) for every flag and environment variable.

## Audit methodology — evidence-grounded, not rubber-stamped

AAA performs an **independent** audit: it does not trust the provider's declared
numbers. For each engagement it

- **loads the real artefacts** uploaded in Stage B (the fitted model, the
  training/evaluation datasets, the governance `.docx` documents) and **re-runs**
  the analysis tools on them — performance metrics, robustness probes, the
  fairness suite, data-quality/PII scans — then diffs the recomputed results
  against the declared `accuracy_metrics`;
- routes every phase artefact through an **independent Verifier** before it is
  admitted;
- **grounds each article verdict in evidence** with a per-article rationale and
  evidence URIs. Article verdicts are `PASS`, `PASS_WITH_OBSERVATIONS`, `FAIL`,
  or `INSUFFICIENT_EVIDENCE` — **absence of evidence is never `PASS`**. A
  non-executable model or an unretrievable governance self-assessment yields
  `INSUFFICIENT_EVIDENCE`, not a pass;
- issues an ISAE-3000-style **auditor opinion**: `unqualified`, `qualified`,
  `adverse` (confirmed non-conformity), or `disclaimer_of_opinion` (a mandatory
  high-risk requirement could not be verified).

Every verdict is **traceable**: agents stamp the MinIO `artefact_uri` and the
retrieved `source_uri`/`locator`s onto each finding and artefact, and the
Verifier reviews them against that evidence. Phase agents also retrieve in a
bounded **ReAct** loop — they seed their core EU AI Act articles and may emit a
`retrieval_plan` to pull additional regulatory/client-document chunks before
concluding. Submitted models may be bare estimators **or** saved bundles
(`{'model': …, 'encoders': …, 'feature_cols': …}`); the auditor unwraps the
bundle, applies the encoders, and scores the model so accuracy/robustness/
fairness are actually verified.

**Human-in-the-loop is defer-and-resolve, not a hard pause.** When the Verifier
escalates an artefact, the pipeline still runs to completion and emits a
**provisional** report (`report_status: PROVISIONAL_PENDING_HITL`) plus an
editable `<id>_hitl_review.json` packet that lists each escalated artefact with
*why* it escalated and the evidence behind it. The packet is also emitted when
review is required for a reason the Verifier did not raise — an adverse verdict
sets `hitl_required` on its own — in which case the cases are derived from the
material findings behind that verdict (`escalation_source: "verdict"`), so a
reviewer is never told to act with nothing to act on. A human fills in each case's
decision, then `python -m scripts.finalize_hitl <id>` folds those decisions back
in, recomputes the matrix, and renders the FINAL report. The packet is reached
through the **admin console** on the results page — the customer sees only a
note saying their report is provisional and that nothing is needed from them.

See [ARCHITECTURE.md §3.2a](./ARCHITECTURE.md) for the full verdict ladder and
§8 for the HITL workflow.

## Documentation

| File | Purpose |
|------|---------|
| [USER_MANUAL.md](./USER_MANUAL.md) | Step-by-step end-user walkthrough of a full audit. |
| [SETUP.md](./SETUP.md) | Technical quick-start, environment variables, and verification commands. |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Full system design and thesis-oriented architecture notes. |
| [PROMPT.md](./PROMPT.md) | Canonical prompt source for the runtime prompt registry. |
| `docs/` (Sphinx) | Auto-generated API reference — build with `make -C docs html`. |
| [infra/runbook.md](./infra/runbook.md) | Operational procedures for the implemented repo. |

## Main surfaces

| Surface | Command | Notes |
|---------|---------|-------|
| Full stack | `make start` / `python -m aaa` | Docker + migrations + API + UI in one command. |
| Streamlit UI | `aaa ui` | Five-step customer wizard ending in a results dashboard; the auditor console (HITL packet, T17/T18, run integrity, raw AuditState) is behind the ⚙ button on it. |
| FastAPI | `aaa api` | REST API with health, workflow, report, and data endpoints. |
| Headless audit | `aaa audit --engagement-id ...` | Smallest end-to-end run of a bundled fixture. |
| Mock case | `python -m scripts.run_mock_case 01_finclear_gmbh` | Full end-to-end run via the API. |
| Finalize HITL | `python -m scripts.finalize_hitl <engagement_id>` | Resolve a provisional report after a human edits the HITL packet. |
| Run preflight | `python -m aaa.tools.run_preflight <case-doc> --intake-dir <bundle>` | Checks a planned run against the baseline a case document pins — model and provider pin, CGSA dialect, Stage A declaration, document slots. Exits non-zero when the run would not be comparable. Run it before any paid run. |
| Fill the wizard | `python -m scripts.wizard_fill --run` | Drives the form with Playwright from the case bundle, labels imported from the wizard's own source. Headed by default; `--run` dispatches the audit and keeps the browser open. Needs the dev set (`requirements-dev.txt`) plus a one-off `playwright install chromium`. |

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
| `data/customer/<company>/<id>_audit_state.json` | Complete final audit-state (served by `/audit-state`) |
| `data/customer/<company>/<id>_T17.json` / `_T18.json` | Compliance matrix + audit report, machine-readable (admin console only) |
| `data/customer/<company>/<id>_hitl_review.json` | Editable HITL review packet (when human sign-off is pending) |
| `data/customer/<company>/<id>_audit_report.pdf` / `_client_report.md` | The two documents the customer is actually offered |

Change the root with `AAA_DATA_DIR=/path/to/data-root`.

## Observability and monitoring

AAA emits structured logs and explicit LLM audit records.

| Path | Contents |
|------|----------|
| `logs/app/app.log` | Root application log |
| `logs/api/api.log` | FastAPI route activity |
| `logs/agents/agents.log` | Agent/runtime logs |
| `logs/audit/llm_audit.log` | Structured audit log stream |
| `logs/audit/llm_audit.jsonl` | One JSON record per LLM call: prompt, reply, tokens, latency, cost |
| `logs/errors/*.jsonl` | Error records written by `capture_error(...)` |

Prometheus metrics are exposed at `GET /metrics`. LLM calls become Langfuse
traces, grouped one session per engagement, once `LANGFUSE_PUBLIC_KEY`/
`LANGFUSE_SECRET_KEY` are set (blank = tracing off, everything above still
works). `make obs` starts an optional Grafana + Prometheus + Loki dashboard
(`http://localhost:3002`) over all of the above — see SETUP.md §8.

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
| `POST` | `/api/v1/engagements/{engagement_id}/run` (`?full=true` returns the audit-state inline) |
| `GET` | `/api/v1/engagements/{engagement_id}/audit-state` (complete final audit-state JSON) |
| `GET` | `/api/v1/engagements/{engagement_id}/hitl-review` (deferred-HITL review packet) |
| `GET` | `/api/v1/engagements/{engagement_id}/report` |
| `GET` | `/api/v1/engagements/{engagement_id}/report.pdf` |

### Persistent data access

| Method | Path |
|--------|------|
| `GET` | `/api/v1/data/engagements` |
| `GET` | `/api/v1/data/results` |
| `GET` | `/api/v1/data/engagements/{engagement_id}/input` |
| `GET` | `/api/v1/data/engagements/{engagement_id}/result` |
| `GET` | `/api/v1/data/engagements/{engagement_id}/result/{summary,findings,compliance}` |

## Repository layout

Every Python module is kept small (≤50 source lines) and the tree follows a
strict **module/sub-module/file** convention repo-wide (both `aaa/` and
`scripts/`): related files live in subpackages (`report_render/pdf/theme.py`,
`wizard/step4/matrix.py`, `scripts/setup/steps/env.py`), never as
underscore-prefixed siblings (`pdf_theme.py`, `steps_env.py`).

```text
UAGF_TAM_AAA/
├── aaa/
│   ├── agents/            # 14-agent system + orchestrator phase modules
│   ├── api/               # FastAPI app, schemas, in-memory runtime store, routers
│   ├── cli/               # sub-commands: run (full audit), report (batch PDFs)
│   ├── data/              # file-based persistence layer
│   ├── integrations/      # switchable S6 XAI / S7 Security providers
│   ├── launcher/          # one-command start-up (`python -m aaa`)
│   ├── observability/     # logging, metrics, error capture, LLM audit
│   ├── platform/          # prompt registry, evidence store, state, model registry
│   ├── tools/             # deterministic audit tools (variants as subpackages)
│   └── ui/                # customer wizard + dashboard, admin console, design system
├── data/                  # persisted demo data + regulatory corpus + fixtures
├── docs/                  # Sphinx documentation source
├── infra/                 # runbook + tofu infrastructure files
├── packages/              # distributable schema package(s)
├── scripts/               # setup, demo, corpus ingestion, fixtures, wizard driver
├── templates/             # canonical T01a–T18 schemas
└── tests/                 # unit, contract, golden, e2e + tracked CI fixtures
```

Customer-facing PDF reports regenerate offline for every company under
`data/customer/` with `python -m aaa report --all` (no LLM calls).

### What the repository does not ship

`docs/` carries the documentation that describes what the system **is**. The
record of what particular **runs did** is not committed: it lives under
`/local/`, which is gitignored whole and explained by `local/README.md`. That is
the per-LLM-call assessment transcripts (up to 1.7 MB each), the
defect-and-fix logs that accompany them, the evidence kept from individual runs,
and the per-run analysis that generates them. They are large, they regenerate
whenever a run is repeated, and several describe a real provider's system.

Case 06 is that provider. `mock/06_mariposa_edu_gmbh/` is their own technical
documentation and `local/assessments/run_2026-09-10/` is a 5 MB per-call
transcript of an audit of it; both stay on the machine that holds them. The
thesis exposé under `data/` is likewise excluded — it belongs to the thesis, not
the codebase.

The intake bundle is handed over separately as `mariposa.zip`; `corpus.zip`
carries the regulatory corpus and the compliance checker, which live under the
untracked `data/`. `python3.12 bootstrap.py` unpacks the two from the repository
root.

Nothing breaks without any of it. Every test that reads this material is
`skipif`-guarded, and `aaa.tools.run_preflight` reports a clear error rather than
a traceback when the case document it is pointed at is absent. The other five
mock cases (`01_finclear_gmbh` … `05_talentsift_gmbh`) are fictional and are
shipped.

Per-run *output* keeps its existing paths, because the code, the Compose mounts
and the dashboards all address it there: `data/` (customer deliverables, the
corpus, the run archive), `logs/`, `screenshots/` and `downloads/` are gitignored
where they are.

## Regulatory corpus

The source materials live under `data/regulatory_corpus/`; `data/` is not
committed, so on a clone they arrive in `corpus.zip` (unpacked by
`bootstrap.py`, which also embeds them). To enable live retrieval by hand,
start Docker services and run:

```bash
python -m scripts.ingest_regulatory_corpus --dry-run -v      # parse + chunk only
python -m scripts.ingest_regulatory_corpus \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

For more detail, see [SETUP.md](./SETUP.md) and [USER_MANUAL.md](./USER_MANUAL.md).
