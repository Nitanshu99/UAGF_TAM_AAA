# SETUP.md — Layman's Setup Guide for AAA (UAGF_TAM_AAA)

> A plain-English, step-by-step guide for someone who is **not a developer**.
> You will: (1) put the right files in the right folders, (2) (optionally) tweak
> a few knobs, (3) install the project, (4) run it.
>
> If you just want a fast smoke test with no data of your own, jump to
> **Section 5 → "Quick path"**. The system ships with a built-in **offline mode**
> that uses sample data and requires no API keys, no LLMs, and no internet.

---

## 0. What you need before you start

| Tool | Why | How to install |
|------|-----|----------------|
| **Python 3.12** (exact) | The whole project runs on it | macOS: `brew install python@3.12` · Windows/Linux: [python.org](https://www.python.org/downloads/) or `pyenv install 3.12` |
| **git** | To clone the repo | macOS: `brew install git` · Windows: [git-scm.com](https://git-scm.com) |
| **Docker Desktop** | Runs Postgres, Qdrant, MinIO locally (only needed for "online" mode) | [docker.com](https://www.docker.com/products/docker-desktop) |
| **GNU Make** (optional) | Lets you type `make demo` instead of long commands | macOS: pre-installed · Windows: install via Chocolatey |

Check that Python is correct:
```bash
python3.12 --version          # should print "Python 3.12.x"
```

---

## 1. The "content folders" — what goes where, at each stage

There are **four places** where you (the user) put files. Each one feeds a
different stage of the pipeline. None of them are mandatory if you stay in
offline/demo mode — the system has built-in fall-backs everywhere.

### 1.1 `data/regulatory_corpus/` — the EU AI Act text (Stage: RegulatoryRAG)

**This folder does not exist yet — you create it.**

```bash
mkdir -p data/regulatory_corpus
```

| What to put inside | Accepted formats | What happens if empty |
|--------------------|------------------|------------------------|
| The full text of the **EU AI Act** (Regulation (EU) 2024/1689), plus any harmonised standards, Commission guidance, Annex documents | `.pdf`, `.txt`, `.md`, `.docx`, `.html` (anything LlamaIndex's `SimpleDirectoryReader` can read) | The system silently falls back to a small **built-in knowledge base** in `aaa/agents/tier1/regulatory_rag.py` covering only Art. 9, 10, 13, 43, Annex III, and GPAI Art. 51. Good enough for demos, not for a real audit. |

**Where to download the EU AI Act:**
- Official PDF: <https://eur-lex.europa.eu/eli/reg/2024/1689/oj>
- Annex III (high-risk uses) and Annex IV (technical documentation) — same URL.

After downloading, drop the file(s) into `data/regulatory_corpus/`.
A one-time ingestion step then loads them into Qdrant (see Section 4).

### 1.2 `scripts/fixtures/uci_german_credit/` — the intake submission (Stage 0)

Already shipped. Contains three JSON files that simulate a client's audit
submission:

```
scripts/fixtures/uci_german_credit/
├── stage_a.json      # Triage: provider name, modality, declared risk tier
├── stage_b.json      # Annex IV dossier (technical documentation)
└── stage_c.json      # Intake completeness report
```

To audit **your own AI system**, copy this folder and edit the three files —
the field names in `stage_a.json` (e.g. `provider_name`, `declared_risk_tier`,
`declared_annex_iii_sections`) tell you what each field expects.

### 1.3 `scripts/fixtures/cgsa/` — the upstream S4 payload (Stage 5)

Already shipped. Contains JSON payloads conforming to
`schemas/cgsa/v1.0.0/uagf_cgsa_aaa_schema.json`. In production this payload
arrives over HTTP from the S4 system; in offline mode it's read from this folder.

To audit your own system you must produce a CGSA payload that matches the
schema. Use `scripts/fixtures/cgsa/uci-german-credit-001.json` as the template
and only change values, never the structure.

### 1.4 `data/files/` — model artefacts (Stage: DataAuditor / ModelValidator)

Optional. If you want the data-quality and model-validation agents to inspect a
real model, drop the model file (`.pkl`, `.onnx`) and its training CSV here.
Otherwise the agents emit deterministic mock metrics.

---

## 2. The "knobs" — what you can tweak, and where

Everything below is **optional**. Defaults work out of the box.

### 2.1 Top-level switches (`.env` file at repo root)

| Variable | Default | What it does |
|----------|---------|--------------|
| `AAA_OFFLINE_MODE` | `false` | `true` = no internet, no LLM calls, no Docker required. Best for the first run. |
| `AAA_LOG_LEVEL` | `WARNING` | Set to `INFO` or `DEBUG` to see what the agents are doing. |
| `LITELLM_MODEL_TIER1` | `claude-opus-4-5` | LLM used by the Orchestrator + Verifier (smartest). |
| `LITELLM_MODEL_TIER2` | `claude-sonnet-4-5` | LLM used by phase agents (ScopeAgent, DataAuditor, …). |
| `LITELLM_MODEL_TIER3` | `claude-sonnet-4-5` | LLM used by on-demand specialists (Cyber, Privacy, …). |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` / `MISTRAL_API_KEY` | empty | Only needed when `AAA_OFFLINE_MODE=false`. Fill in at least one. |
| `QDRANT_URL` | `http://localhost:6333` | Where the Qdrant vector store listens (Docker default). |
| `QDRANT_COLLECTION` | `regulatory_corpus` | Name of the primary Qdrant hybrid collection (dense + sparse). Populated by `scripts/ingest_regulatory_corpus.py`. |
| `CGSA_FIXTURE_DIR` | `scripts/fixtures/cgsa` | Where the offline CGSA payloads live. Empty = pull live from S4 over HTTP. |
| `DATABASE_URL` | `postgresql://aaa:changeme@localhost:5432/aaa` | Postgres connection (used by LangGraph checkpointing and the FastAPI Platform). |

To change any of these, open `.env` (created by the setup script — see Section 3)
in a text editor and edit the value after the `=`.

### 2.2 Chunking & embedding (Stage: RegulatoryRAG ingestion)

The ingestion pipeline (`scripts/ingest_regulatory_corpus.py`) uses **per-legal-unit chunking** — `SentenceSplitter` is applied separately to each article, recital, annex, clause, and control so that no chunk ever spans two legal boundaries.

| Knob | Default | How to change |
|------|---------|---------------|
| Chunk size | **800 tokens** | `--chunk-size N` flag |
| Chunk overlap | **100 tokens** | `--chunk-overlap N` flag |
| Dense embedding model | `text-embedding-3-large` (OpenAI, 3072-dim) | Edit `DENSE_MODEL` in the script |
| Sparse embedding model | `Qdrant/bm25` (fastembed) | Edit `SPARSE_MODEL` in the script |
| PDF parsing backend | `pypdfium2` (ISO/IEC 42001) | `pypdfium2>=5.8.0` in `requirements.txt`; handles non-standard PDF token layouts that `pdfplumber` cannot read |
| Fusion strategy | **RRF** (Reciprocal Rank Fusion) | Qdrant server-side; change in `_vector_search` |
| Similarity top-k | **5** (per query) | Pass `top_k=...` when calling `RegulatoryRAG.search(query, top_k=...)` |

See Section 4 for the full ingestion command and flags.

### 2.3 Audit thresholds (Stage: completeness gate & verdict)

| Knob | Default | Where |
|------|---------|-------|
| Intake completeness gate (Stage 0) | **≥ 0.80** | `aaa/tools/intake_completeness_calculator.py` |
| Phase completeness score | weights per phase | `aaa/tools/completeness_score.py` |
| Regulatory coverage % | tracked as KPI 2 | `aaa/tools/regulatory_coverage.py` |

These are deterministic Python; edit the constants at the top of each file if
you need to relax/tighten the gate.

### 2.4 Prompts (Stage: Verifier, ScopeAgent, etc.)

The Verifier uses a **system + user message split** so that the static rubric is
byte-identical across every call (enabling server-side prefix caching) and
untrusted artefact content is isolated in a separate user message wrapped in
XML data tags.

| Symbol | File | Purpose |
|---|---|---|
| `_SYSTEM_PROMPT` | `aaa/agents/tier1/verifier.py` | Static rubric, chain-of-thought instruction, security policy, and JSON output contract — never changes per call |
| `_build_critique_messages()` | `aaa/agents/tier1/verifier.py` | Builds the `[system, user]` message list; wraps artefact body in `<artefact>` tags and evidence URIs in `<evidence_uris>` tags |
| inline prompt | `aaa/agents/tier2/scope_agent.py` | Scope classification instructions |
| `_DANGEROUS_PATTERNS` | `aaa/tools/prompt_injection_suite.py` | Adversarial probe patterns for prompt-injection testing |

To change the audit wording, edit `_SYSTEM_PROMPT` in `verifier.py` **and** update
the corresponding snapshot in `tests/unit/test_prompt_snapshots.py` in the same
commit so the snapshot tests remain in sync.

### 2.5 Model registry & Flex Processing

All 12 agents pull their default LLM model and OpenAI **service tier** from a
single source of truth at [`aaa/platform/model_registry.py`](./aaa/platform/model_registry.py).

#### Redistributed model assignment

| # | Agent | Model | Service tier |
|---|-------|-------|--------------|
| 1 | Orchestrator | `gpt-5.5` | standard |
| 2 | Verifier | `gpt-5.5` | **flex** |
| 3 | Regulatory RAG | `gpt-5.4-nano` | standard |
| 4 | ScopeAgent | `gpt-5.4` | standard |
| 5 | DataAuditor | `gpt-5.4` | standard |
| 6 | ModelValidator | `gpt-5.5` | **flex** |
| 7 | OutputFairnessTester | `gpt-5.4-mini` | standard |
| 8 | GovernanceAgent | `gpt-5.5` | **flex** |
| 9 | ReportArchitect | `gpt-5.4` | **flex** |
| 10 | UAGF-TAM-L | `gpt-5.5` | **flex** |
| 11 | CyberSecurityAgent | `gpt-5.4` | standard |
| 12 | PrivacyDPOAgent | `gpt-5.4` | standard |

#### What is Flex Processing?

OpenAI Flex (`service_tier="flex"`) routes requests to spare capacity and
charges **~50 % less** than the standard rate.  The trade-off is that the API
may respond with `429 Resource Unavailable` during peak load and that latency
can be higher.

The five **non-interactive** agents (Verifier, ModelValidator, GovernanceAgent,
ReportArchitect, UAGF-TAM-L) run on Flex because:

* They are invoked asynchronously, off the critical user-facing path.
* Their prompts are long (full artefact + evidence), making the discount
  financially significant.
* A delayed response is acceptable; a blocked audit head is not.

Interactive / critical-path agents (Orchestrator, ScopeAgent, etc.) stay on
the standard tier to guarantee low latency.

#### Retry and fallback behaviour

[`aaa/platform/flex_retry.py`](./aaa/platform/flex_retry.py) wraps every
`litellm.acompletion` call made through `BaseAgent.acompletion()`:

| Setting | Value | Purpose |
|---------|-------|---------|
| Flex timeout | **600 s** (10 min) | Flex may queue before processing |
| Standard timeout | **120 s** | Normal calls |
| Max Flex retries | **3** | Retry on `429 / RateLimitError` |
| Backoff | **2ˢ s** (2 → 4 → 8 s) | Exponential back-off |
| Fallback | **standard tier × 1** | Used after all Flex retries fail |

If all Flex retries and the standard-tier fallback also fail, a `RuntimeError`
is raised and the Verifier's existing exception handler falls back to the
deterministic offline critique — so the audit always produces a result.

#### How to override defaults

Every agent constructor accepts explicit `model=` and `service_tier=` keyword
arguments that take precedence over the registry:

```python
from aaa.agents.tier1.verifier import Verifier

# Force a different model for testing:
v = Verifier(model="gpt-4o", service_tier="default")
```

To change the roster-wide default for an agent, edit the `AGENT_MODELS` dict
in `aaa/platform/model_registry.py`.

---

## 3. Installation (one command)

From the repo root:

```bash
python3.12 scripts/setup.py
```

That's it. The script will:

1. Verify your Python is 3.12.
2. Create a `.venv/` virtual environment (an isolated Python world for the project).
3. Install all Python dependencies.
4. Copy `.env.example` → `.env` (so you have something to edit).
5. Start the Docker services (Postgres, Qdrant, MinIO, …) if Docker is running.
6. Apply database migrations.
7. Run an offline smoke test to confirm everything works.

If you don't have Docker installed and just want to try offline mode:
```bash
python3.12 scripts/setup.py --no-docker --no-migrate
```

After the script finishes, **activate** the virtual environment in every new
terminal you open:
```bash
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows
```

---

## 4. (Optional) Load the EU AI Act into Qdrant

Only needed if you put PDFs in `data/regulatory_corpus/` and want real
RAG (not the built-in offline KB). Skip this section for the first run.

### 4.1 Make sure Qdrant is running

```bash
docker compose up -d qdrant
curl http://localhost:6333/healthz       # should print "healthz check passed"
```

### 4.2 Run the ingestion script

`scripts/ingest_regulatory_corpus.py` is already committed. It handles EU AI Act, GDPR (EUR-Lex HTML) and ISO/IEC 42001 (PDF) in one pass, producing a hybrid dense + sparse Qdrant collection.

> **Environment variables are loaded automatically.** The script calls `python-dotenv`'s `load_dotenv()` at startup, so it reads your `.env` file without you having to run `source .env` first. Just make sure `.env` has `OPENAI_API_KEY` and `QDRANT_URL` set.

> **macOS users:** on the first run after installing new native extensions (e.g. `qdrant_client`, `sklearn`, `nltk`), macOS Gatekeeper may verify the `.so` files, which can take 10–30 s per library. The script pre-imports these libraries early in `main()` so the delay happens upfront rather than mid-run. If the script appears to hang during the first few seconds, simply wait — it will proceed automatically.

**Dry-run first** (parses and chunks everything; no Qdrant writes, no OpenAI calls):

```bash
python3.12 scripts/ingest_regulatory_corpus.py --dry-run -v
```

Expected output includes lines such as:
```
[dry-run] EU_AI_Act   →  339 chunks (136 articles, 181 recitals, 22 annexes)
[dry-run] GDPR        →  288 chunks (115 articles, 173 recitals)
[dry-run] ISO_IEC_42001 →  88 chunks (32 clauses, 56 controls)
[dry-run] total        → 715 corpus chunks; 15 obligation-question points
```

**Full ingestion** (requires `OPENAI_API_KEY` and a running Qdrant):

```bash
python3.12 scripts/ingest_regulatory_corpus.py \
    --corpus data/regulatory_corpus \
    --checker data/files/eu_ai_act_compliance_checker.json \
    --collection regulatory_corpus \
    --obligations-collection obligations_index
```

The script is **idempotent**: every chunk gets a deterministic SHA-256 point ID from `text + regulation + ref + chunk_index`. On re-run it skips any chunks already present in Qdrant — no extra OpenAI API calls are made.

**Reset and re-ingest** (drops and recreates both collections):

```bash
python3.12 scripts/ingest_regulatory_corpus.py --reset
```

All flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--corpus` | `data/regulatory_corpus` | Directory containing HTML / PDF source files |
| `--checker` | `data/files/eu_ai_act_compliance_checker.json` | Compliance-checker JSON for metadata enrichment |
| `--collection` | `regulatory_corpus` | Qdrant corpus collection name |
| `--obligations-collection` | `obligations_index` | Qdrant obligations collection name |
| `--chunk-size` | `800` | Tokens per chunk |
| `--chunk-overlap` | `100` | Token overlap between consecutive chunks |
| `--dry-run` | off | Parse + chunk only; no embedding or Qdrant writes |
| `--reset` | off | Drop and recreate both collections before ingestion |
| `--skip-obligations` | off | Skip ingesting the obligations_index collection |
| `-v` | off | Verbose logging |

You only need to re-run the script when you add or change files in `data/regulatory_corpus/`.

---

## 5. Running the project

Activate the venv first (`source .venv/bin/activate`).

### 5.1 Quick path — offline demo, no API keys, no Qdrant

```bash
make intake-demo
```
(or, without Make:)
```bash
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
python -m aaa.cli run \
  --engagement-id eng-demo-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```
Prints a JSON summary with the final verdict (PASS / PASS_WITH_OBSERVATIONS / FAIL).

### 5.2 Streamlit UI (point-and-click)

```bash
AAA_OFFLINE_MODE=true streamlit run aaa/ui/app.py
```
Open the URL it prints (usually `http://localhost:8501`).

### 5.3 FastAPI backend (for integrations)

```bash
uvicorn aaa.api.main:app --reload --port 8000
```
Browse to `http://localhost:8000/docs` for the interactive API explorer.

### 5.4 Full online run (real LLMs, real Qdrant, real Postgres)

1. Fill in at least one LLM key in `.env` (`ANTHROPIC_API_KEY=…`).
2. Make sure Docker is up: `docker compose up -d`.
3. Ingest the EU AI Act corpus (Section 4).
4. Run **without** `--offline`:
   ```bash
   python -m aaa.cli run \
     --engagement-id eng-prod-001 \
     --intake-dir scripts/fixtures/uci_german_credit \
     --output-file out/eng-prod-001.json
   ```

---

## 6. Where to look next

| If you want to … | Read |
|------------------|------|
| Understand the agent design | `ARCHITECTURE.md` |
| Day-to-day developer commands | `USER_MANUAL.md` |
| Production deployment / on-call | `infra/runbook.md` |
| What's been implemented | `tasks.md` |

---

## 7. If something breaks

1. Re-run the setup script — it's idempotent: `python3.12 scripts/setup.py`.
2. Make sure your venv is active: `source .venv/bin/activate`.
3. For a clean Docker reset: `docker compose down -v && docker compose up -d`.
4. Try offline mode to isolate the failure: `export AAA_OFFLINE_MODE=true`.
5. See the **Troubleshooting** table in `USER_MANUAL.md` §9.

### Ingestion-specific issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Ingestion script appears to hang (no output) on macOS | macOS Gatekeeper verifying new native `.so` extensions | Wait 10–30 s; the warm-up block pre-imports heavy libs early so this only happens once per new install |
| `loaded 0 units from ISO:IEC 42001-2023.pdf` | Wrong PDF backend (pdfplumber) | Upgrade to `pypdfium2>=5.8.0`: `pip install "pypdfium2>=5.8.0"` |
| `OPENAI_API_KEY not set` | `.env` not found or key missing | The script loads `.env` automatically via `python-dotenv`; ensure `.env` exists at the repo root with `OPENAI_API_KEY=sk-…` |
| Re-run embeds all chunks again | SHA-256 ID mismatch (text changed) | If you change chunking parameters, run `--reset` to drop and recreate the Qdrant collections |
