# User Manual — EU AI Act Compliance Audit System

**Who this is for:** Someone who has cloned this repository and wants to run the
current implementation successfully — even with no prior experience of the
codebase.

This manual reflects the codebase as it exists today: a one-command launcher,
modular FastAPI routes, file-based persistence under `data/`, and structured
logs under `logs/`.

---

## What does this system do?

In plain English: you upload your AI system's technical documents, answer 8
short questions, and this system automatically checks whether your AI system
complies with the EU AI Act. It reads your documents, fills in a compliance
form, runs 13 AI agents behind the scenes, and gives you a downloadable report.

Crucially, this is an **independent** audit — it does **not** just take your
declared numbers at face value. If you upload your trained model and evaluation
dataset, the system re-runs the accuracy, robustness, and fairness tests
**itself** and compares the results to what you declared. Each EU AI Act article
gets one of four verdicts:

- **PASS** — verified, no issues.
- **PASS WITH OBSERVATIONS** — verified, minor things to note.
- **FAIL** — a confirmed problem (e.g. the model fails a fairness test, or the
  data contains undeclared special-category personal data).
- **INSUFFICIENT EVIDENCE** — the system *could not verify* a requirement (for
  example, the model file wasn't a real runnable model). This is **not** a pass.

The report also states a formal **auditor opinion**: *unqualified* (clean),
*qualified* (pass with observations), *adverse* (fail), or *disclaimer of
opinion* (a mandatory high-risk requirement could not be independently verified,
so conformity cannot be concluded).

---

## The short version (for the impatient)

```bash
python3.12 -m scripts.setup --no-docker --no-migrate   # one-time setup
source .venv/bin/activate                              # activate the environment
make start                                             # start everything
```

`make start` (equivalently `python -m aaa`) launches every configured component
— Docker infrastructure, database migrations, the FastAPI backend, and the
Streamlit UI — from a single command. Then open **http://localhost:8501**.

The rest of this manual explains each step, how to configure what starts, and
how to read the results.

---

## Part 1 — Before you start: install the prerequisites

### Step 1.1 — Check whether you have Python 3.12

Open your Terminal (Mac/Linux) or Command Prompt (Windows) and type:

```
python3 --version
```

You should see `Python 3.12.x`. If you see 3.11 or lower, or an error, follow
Step 1.2. If you already have 3.12, skip to Step 1.3.

> **What is the Terminal?** On a Mac: press `Cmd + Space`, type "Terminal",
> press Enter. On Windows: press `Win + R`, type `cmd`, press Enter. On Linux:
> `Ctrl + Alt + T`.

### Step 1.2 — Install Python 3.12

**Mac / Windows:** download the 3.12 installer from
`https://www.python.org/downloads/` and run it. On Windows, tick **"Add Python
to PATH"** on the first installer screen. Reopen your Terminal and verify with
`python3.12 --version`.

**Linux (Ubuntu/Debian):**
```
sudo apt update
sudo apt install python3.12 python3.12-venv
```

### Step 1.3 — Make sure you're in the right folder

Navigate to where you cloned the repository (the folder containing `README.md`,
`aaa/`, and `scripts/`):

```
cd /path/to/UAGF_TAM_AAA
```

Confirm with `ls` (Mac/Linux) or `dir` (Windows) — you should see `README.md`,
`Makefile`, and the `aaa/` folder.

---

## Part 2 — One-time setup

**The one-command way.** If you were given `mariposa.zip` and `corpus.zip`, put
both in the repository folder and run:

```
python3.12 bootstrap.py
```

It asks for your OpenRouter key once (hidden input) and then does everything
in Parts 2–7 for you: the virtual environment, `.env`, the bundles, Docker,
the legal corpus, the servers, and a browser window with every service
dashboard in its own tab and the Mariposa audit filled in and running in
front. Leave the window open; the results appear in it. Press `Ctrl + C` in the
terminal when you are done (the Docker containers keep running and keep their
data). Re-running it is safe — finished steps are skipped.

`python3.12 bootstrap.py --mock-llm` does the same without spending anything
(a local stand-in answers instead of OpenRouter, so the verdicts are the
deterministic fallbacks, not a real audit) — useful to check the machine
before a paid run.

**The step-by-step way.** From the repository root, run the setup script. It
creates the virtual environment, installs dependencies, and creates your `.env`
file:

```
python3.12 -m scripts.setup --no-docker --no-migrate
```

The `--no-docker --no-migrate` flags give you the lightweight laptop setup (no
containers, no database). Drop them later if you want the full stack.

`python -m scripts.setup` runs these idempotent steps:

1. verifies Python ≥ 3.12
2. creates `.venv`
3. installs dependencies
4. creates `.env` from `.env.example` if missing
5. optionally starts Docker services
6. optionally applies database migrations
7. runs a quick test suite as a smoke check

If it finishes with **"✓ Setup complete"**, you're ready.

> **Manual alternative.** If the bootstrap fails, you can do it by hand:
> `python3.12 -m venv .venv`, then `source .venv/bin/activate`, then
> `pip install -r requirements-dev.txt`, then `cp .env.example .env`.

---

## Part 3 — Activate the virtual environment (every session)

Every time you open a new Terminal to work with the project, activate the
environment first:

**Mac/Linux:** `source .venv/bin/activate`
**Windows:** `.venv\Scripts\activate`

You'll know it worked when your prompt shows `(.venv)` at the start. To leave it
later, type `deactivate`.

---

## Part 4 — Configure `.env` (optional)

The bootstrap created a `.env` file with working defaults, so you can run the
quick demo without editing anything.

Two groups of settings matter:

**Launch plan** — controls what `make start` brings up:

| Setting | Default | Effect |
|---------|---------|--------|
| `AAA_LAUNCH_DOCKER` | `auto` | Start Docker infra (`auto`/`true`/`false`). |
| `AAA_LAUNCH_MIGRATE` | `auto` | Run database migrations on start. |
| `AAA_LAUNCH_API` | `true` | Start the FastAPI backend. |
| `AAA_LAUNCH_UI` | `true` | Start the Streamlit UI. |
| `PLATFORM_PORT` | `8000` | FastAPI port. |
| `STREAMLIT_SERVER_PORT` | `8501` | Streamlit port. |

For example, to launch only the UI, set `AAA_LAUNCH_API=false`.

**Real LLM analysis** — for a full audit backed by a language model, add your
key:

```
OPENAI_API_KEY=sk-your-key-here
```

Without a key, the agents still run but fall back to deterministic, rule-based
analysis — fine for learning the workflow, but not a substitute for a real audit.

---

## Part 5 — Choosing where embeddings run

To search text by meaning rather than by keyword, the system turns text into
lists of numbers called **embeddings**. Producing them is the one step that can
send your documents to a third party — so you choose, per place, whether that
happens on OpenAI's servers or on your own machine.

### The three places text gets embedded

| Setting | What it embeds | Why you might keep it local |
|---------|----------------|-----------------------------|
| `EMBEDDINGS_CLIENT_DOCS` | The **customer's own** compliance dossier — the files uploaded in the wizard | This is confidential client documentation. Sending it to a third-party API is exactly the data-governance issue this tool would flag in an auditee. |
| `EMBEDDINGS_REGULATORY` | Search queries against the EU AI Act corpus | The corpus is public law, so there is little to protect — but you may want the system to work with no internet at all. |
| `EMBEDDINGS_EVIDENCE` | Internal re-ranking of evidence snippets | Small, internal text. Mostly a cost and offline question. |

They are **separate on purpose**. The common setup keeps the client's documents
on your machine while letting the public legal corpus use the higher-quality
hosted model. One global switch would force you to trade one against the other.

### The settings

| Setting | Values | Default |
|---------|--------|---------|
| `EMBEDDINGS_CLIENT_DOCS` | `openai`, `openrouter` or `local` | `openai` |
| `EMBEDDINGS_REGULATORY` | `openai`, `openrouter` or `local` | `openai` |
| `EMBEDDINGS_EVIDENCE` | `openai`, `openrouter` or `local` | `openai` |
| `EMBEDDINGS_LOCAL_MODEL` | a sentence-transformers model name | *(none — you must choose)* |

`EMBEDDINGS_LOCAL_MODEL` deliberately has no default. Picking one for you would
silently decide a quality-versus-download-size trade-off, and would let your
search index get built from a model nobody chose. Reasonable options:

| Model | Size | Vector width | Notes |
|-------|------|--------------|-------|
| `all-MiniLM-L6-v2` | ~80 MB | 384 | Fast on a laptop CPU. Good starting point. |
| `all-mpnet-base-v2` | ~420 MB | 768 | Noticeably better search, several times slower. |
| `BAAI/bge-m3` | ~2.2 GB | 1024 | Strongest, handles non-English text, wants a GPU. |

### Three setups

**A — Everything hosted (the default).** Nothing to do. Leave the settings
alone and make sure `OPENAI_API_KEY` is set.

**A′ — Everything hosted, one key.** `openrouter` is the same OpenAI embedding
model reached through OpenRouter, so a `.env` with `PROVIDER=openrouter` needs
only `OPENROUTER_API_KEY`. This is what `bootstrap.py` writes:

```
EMBEDDINGS_CLIENT_DOCS=openrouter
EMBEDDINGS_REGULATORY=openrouter
EMBEDDINGS_EVIDENCE=openrouter
```

**B — Keep the client's documents private.** The most common real-world choice:

```
EMBEDDINGS_CLIENT_DOCS=local
EMBEDDINGS_LOCAL_MODEL=all-MiniLM-L6-v2
```

Uploaded customer files are now embedded on your machine and never leave it.
The legal corpus keeps using OpenAI, so **no re-ingest is needed**.

**C — Fully offline.** No text leaves your machine at any point:

```
EMBEDDINGS_CLIENT_DOCS=local
EMBEDDINGS_REGULATORY=local
EMBEDDINGS_EVIDENCE=local
EMBEDDINGS_LOCAL_MODEL=all-MiniLM-L6-v2
```

Because this changes `EMBEDDINGS_REGULATORY`, you **must rebuild the legal
corpus** (see below). Note that the audit agents themselves still call an LLM;
this setting only controls embeddings.

### Changing `EMBEDDINGS_REGULATORY` means rebuilding the corpus

Different models produce different-sized vectors — OpenAI's is 3072 numbers
wide, `all-MiniLM-L6-v2` is 384. A search index built by one model cannot be
searched by another. After changing this setting, rebuild it:

```bash
python -m scripts.ingest_regulatory_corpus --reset
```

Until you do, the system **refuses to search** rather than returning
confident-looking but meaningless results. It records which model built the
corpus and checks that on every search, so even swapping between two models of
the *same* width is caught.

`EMBEDDINGS_EVIDENCE` needs no rebuild — evidence re-ranking is computed fresh
on every run and stores nothing.

`EMBEDDINGS_CLIENT_DOCS` needs no rebuild either, but is worth understanding.
Uploaded documents are indexed **once per engagement** and reused afterwards:

- **New engagements** pick up the new setting automatically.
- **Engagements already indexed** still hold vectors from the previous model.
  Re-opening one after switching is detected and refused — the search returns no
  hits and logs an error naming the mismatch, rather than matching new queries
  against old vectors. To use the new model for such an engagement, re-upload
  its documents under a fresh engagement ID.

### If something goes wrong

**`EMBEDDINGS_LOCAL_MODEL is unset. Selecting a 'local' embedding provider
requires naming the sentence-transformers model to use...`** — you set a path to
`local` without choosing a model. Add `EMBEDDINGS_LOCAL_MODEL` (see the table).

**`collection 'eu_ai_act' was embedded with 'local:all-mpnet-base-v2' but
EMBEDDINGS_REGULATORY resolves to 'openai:text-embedding-3-large'.`** — the
corpus was built by a different model than the one now configured. Either
rebuild it with `--reset`, or put the setting back to what it was.

**`collection 'eu_ai_act' holds 384-dimensional vectors but
EMBEDDINGS_REGULATORY resolves to ... (3072-dimensional).`** — the same problem
on a corpus built before the system started recording model names. Same fix.

**`Corpus 'eu_ai_act' carries no embedding-model stamp...`** — a warning, not an
error. Your corpus predates this check, so only its width could be verified.
Searching still works; rebuild it when convenient to remove the warning.

**First local run is slow.** The model is downloaded once, then cached in your
home directory. Later runs start immediately.

**Note:** a `local` setting needs no `OPENAI_API_KEY` for that path — the system
will not tell you embeddings are unavailable just because no key is present.

---

## Part 6 — Running the system

### The one-command way (recommended)

With the environment active:

```
make start
```

(equivalently `python -m aaa`). This reads `.env` and starts each enabled
component. When it's up:

- **Streamlit wizard:** http://localhost:8501
- **Swagger API docs:** http://localhost:8000/docs

To stop everything, press `Ctrl + C` in that Terminal.

### Running a single surface

If you only want one component, use the subcommands (no `.env` juggling needed):

```
aaa ui                          # Streamlit wizard only
aaa api                         # FastAPI backend only
aaa audit --engagement-id demo  # headless audit of a sample fixture
```

### Walking through the 5-step wizard

Open http://localhost:8501 and follow the steps:

**Step 0 — Get started.** Enter your **company name** and what the **AI system
is called**, then click **Start my audit**. There is no engagement id to invent:
one is derived from your company name (`eng-mariposa-edu-gmbh-1a2b3c`) and shown
on the results page so you can quote it. The two names you enter here are
carried into the Stage A form in step 3, where they take precedence over
anything the extractor reads out of your documents.

**Step 1 — Your documents.** These are indexed into this engagement's document
collection, which is what the audit phases retrieve and quote as evidence. The
wizard no longer runs an LLM over them to pre-fill the form — see *No AI
pre-fill in the wizard* below. Three upload zones:
- **Technical documents** — any PDF/Word/text describing your system (model
  card, datasheet, risk assessment). You may skip this.
- **Model artefact** — your trained model (`.joblib`/`.pkl`). This is what lets
  the audit *independently* re-run accuracy/robustness/fairness tests instead of
  trusting your declared numbers. Without a runnable model, the relevant
  Article 15 / fairness checks come back **INSUFFICIENT EVIDENCE**, not PASS.
- **Datasets** — training and evaluation data (CSV/Parquet). The evaluation set
  is re-scored; the training set is re-scanned for data quality and undeclared
  personal data (Article 10).

  *Tip:* declare which column is the prediction target and which are protected
  attributes in Stage B (`target_column`, `positive_label`,
  `sensitive_feature_columns`). If you don't, the system infers them and records
  the assumption as an observation.

**Step 2 — A few questions.** Answer 8 questions about your system (provider vs
deployer, who uses it, whether it handles personal or sensitive data, whether
it's general-purpose AI, whether it's high-risk, third-party verification, and
EU territories). Click **Continue**.

**Step 3 — Check the details.** Complete the **Stage A** (system declaration)
and **Stage B** (technical documentation) fields; each has an inline
description. Above the form:

- the **How complete this is** meter, which must reach **80%** before you can
  run, and the **scope** verdict;
- **What is still missing** — the outstanding Annex IV sections, named in plain
  language, ranked by how many points each is worth, with the tab each lives
  under. Only 14 fields across the nine sections move the gate, and the sections
  are not worth the same (§1 is worth 20 points, §8 and §9 five each), so this
  panel is the difference between filling in forty boxes and filling in the
  right six.

The form itself is three tabs — **Your system**, **The dossier**, and
**Documents, model & data**. Uploads in the third tab are banded: required of
every system, LLM/agentic-only (collapsed unless your declared modality is one
of those, but never hidden — a composite system like an NLP ranker plus an LLM
interviewer declares one scalar modality and still needs the other band), and
optional model/data artefacts.

When the meter clears 80% and the scope card says your system is in scope, click
**Confirm & Run Audit**.

### No AI pre-fill in the wizard

`DocIntelligenceAgent` used to do two things on upload: index the documents, and
spend an LLM call reading Stage A/B values out of them to pre-fill step 3. The
wizard now does only the first.

- **What you lose:** the review form starts empty; it is filled in by hand.
- **What is unaffected:** the audit runs on what you confirm in the form, and
  the *collection* built at upload time is still what phases 1–5 and the scope /
  data / model / governance agents retrieve against. `IntakeValidator` only
  indexes the seven named Stage B URI fields, so free-form technical
  documentation reaches the audit through the step-1 ingest and no other route.
- **What still offers pre-fill:** `POST /api/v1/engagements/{id}/extract-triage`
  is unchanged and still returns a populated `DocExtractionResult`.

### You are never asked for a CGSA assessment ID

Step 3 used to carry a "CGSA assessment ID (optional)" field. S4 mints that
identifier and files the assessment against an organisation and a system; the
organisation it describes never sees it, so the field could only be filled by
someone with access to this repository.

It is now looked up from the provider and system names you gave in step 0
(`aaa.tools.cgsa_pull.resolve_assessment_id`), and step 3 tells you what was
found in plain words. Two rules matter:

- **No match, or more than one, means none is attached.** Guessing between two
  assessments would put another system's governance history in your report.
- **An evaluated export beats a self-assessment of the same system.** Only an
  evaluated export (`s5-aaa-adapter-v1.0`) carries the threshold a control has
  to fall below, so only it can raise a control-level non-conformity. A
  self-assessment export (`1.0.0`) has scores and prose and no thresholds; the
  form says so, because it changes what the audit can conclude.

### Checking a run before you pay for it

`python -m aaa.tools.run_preflight <case-doc> --intake-dir <bundle>` compares a
planned run with the baseline that case's document pins — the model and provider
pin, the CGSA dialect, the Stage A declaration and the document slots — and
exits non-zero when the run would not be comparable. It takes about a second and
makes no LLM calls.

If you declared an **LLM or agentic** system, Stage B also shows a **Model
provenance** block. Most generative systems run weights the provider does not
own — a vendor endpoint, or a base model plus an adapter — so there is no file
to upload. Answer "How is the model made available?" first; the form then asks
only what your chosen vendor needs to identify the exact model. The auditor
never asks for, and never stores, model weights.

The one answer worth care is the **version pin**. A commit SHA, a dated
snapshot, a container image digest or an ARN identifies weights that cannot
change underneath you; `latest` and `main` do not, and an audit pinned to a
moving alias cannot state which model it actually assessed. The form flags a
branch name or `latest` rather than accepting it silently.

**Step 4 — Results.** A spinner shows the pipeline running; after 10–60 seconds
you get a colour-coded verdict banner, three KPI scores, the compliance matrix,
and download buttons.

---

## Part 7 — Full run with real LLM analysis

For a real audit (live regulatory retrieval + provider-backed LLM agents),
enable the full stack.

**Step 7.1 — Install Docker Desktop** if you don't have it
(`https://www.docker.com/products/docker-desktop/`).

**Step 7.2 — Add your key** to `.env`. With the default `PROVIDER=openai`:
```
OPENAI_API_KEY=sk-your-key-here
```
With `PROVIDER=openrouter` (what `bootstrap.py` sets), the one key is
`OPENROUTER_API_KEY`, and the three `EMBEDDINGS_*` settings should read
`openrouter` too (Part 5, setup A′).

**Step 7.3 — Ingest the regulatory corpus** (first time only, ~5 minutes; also
required again if you change `EMBEDDINGS_REGULATORY` — see Part 5). With
Docker running:
```
python -m scripts.ingest_regulatory_corpus --dry-run -v          # parse + chunk check
python -m scripts.ingest_regulatory_corpus \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

**Step 7.4 — Start everything:**
```
make start
```

Because `AAA_LAUNCH_DOCKER` and `AAA_LAUNCH_MIGRATE` default to `auto`, the
launcher brings up the containers and applies migrations for you before starting
the API and UI. Open http://localhost:8501 and run an audit as in Part 6.

**Step 7.5 — Where inputs, results, and logs live.** See Part 9 and the tables
below.

**Step 7.6 — Stopping.** Press `Ctrl + C` in the launcher Terminal, then stop
the containers (this keeps your data):
```
docker compose down
```
> Only `docker compose down -v` deletes the data volumes — don't add `-v` unless
> you want a completely fresh start.

**Step 7.7 — Watching a run live (optional).** Two ways to see what the
agents are actually doing, beyond the wizard's own progress messages:

- **Langfuse (LLM call tracing)** — already running at
  `http://localhost:3003`. First visit: create a project, then paste its API
  keys into `.env` as `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` (blank =
  no tracing sent, harmless). Once set, every LLM call groups into one
  session per engagement — open the session for your `engagement_id` to see
  every agent's prompts, responses, tokens, and cost in order.
- **Grafana dashboard (metrics + logs)** — not started by default. Run
  `make obs` once, then open `http://localhost:3002` for a live dashboard:
  LLM cost/latency/tokens by agent, phase timing, pass/fail counts, and a
  searchable log panel covering every run (including history already in
  `logs/audit/llm_audit.jsonl` — nothing needs to be "live" to show up here).
  Stop it independently of everything else with `make obs-down`.

Neither is required — `logs/audit/llm_audit.jsonl` always has the full
record regardless.

---

## Part 8 — Troubleshooting

**`python3.12: command not found`** — install Python 3.12 (Part 1, Step 1.2).

**`ModuleNotFoundError` / `No module named 'aaa'`** — the virtual environment
isn't active. Run `source .venv/bin/activate` (Mac/Linux) or
`.venv\Scripts\activate` (Windows), and make sure you're in the repo root.

**`make start` runs but nothing opens** — check `.env`: `AAA_LAUNCH_UI` or
`AAA_LAUNCH_API` may be `false`. Also open http://localhost:8501 manually.

**`Address already in use: port 8501`** — something is already on that port.
Change `STREAMLIT_SERVER_PORT` in `.env`, or run `aaa ui` after stopping the
other process.

**"Intake completeness is X% — reach the 0.80 gate"** — fill in more Step 3
fields. The usual culprits: general description (≥ 50 chars), intended purpose
(≥ 20 chars), performance metrics (valid JSON like `{"accuracy": 0.78}`),
training data description (≥ 30 chars).

**Docker services won't start** — inspect with `docker compose logs postgres`
(or `qdrant`). Common causes: a port conflict (change it in `.env`), low disk
space (`docker system prune`), or Docker Desktop needing a restart. Then
`docker compose down && docker compose up -d`.

**"OpenAI API error" / "AuthenticationError"** — your key in `.env` is missing
or wrong. Confirm it starts with `sk-`, has no stray spaces, and that your
account has credit.

**The audit gives FAIL / INSUFFICIENT_EVIDENCE with little detail** — without an
OpenAI key the agents use conservative rule-based fallbacks. Add a key and upload
a real runnable model + dataset for meaningful, evidence-grounded verdicts.

**Inspect what was persisted** — look under `data/results/<id>/`, or query the
API:
```
curl http://localhost:8000/api/v1/data/engagements/<id>/result
```

**Inspect the LLM audit trail** — open `logs/audit/llm_audit.jsonl`; each line is
one call (messages, response, tokens, latency, cost).

**Start completely fresh** — `rm -rf .venv .env` (Windows: `rmdir /s /q .venv`
then `del .env`), then redo Part 2.

---

## Part 9 — Understanding the output

### Final verdict

| Verdict | What it means |
|---------|--------------|
| **PASS** | All critical requirements are met and **independently verified**. Regulatory coverage ≥ 90%. |
| **PASS WITH OBSERVATIONS** | Verified, but with minor gaps or some requirements that couldn't be independently verified. |
| **FAIL** | A **confirmed** non-conformity: e.g. the model fails a fairness/robustness test, undeclared special-category data, or a declared metric refuted by re-computation. |

Individual articles can also be **INSUFFICIENT EVIDENCE** — the audit couldn't
verify that requirement (e.g. an unrunnable model, or an unretrievable governance
self-assessment). This is **not** a pass; when it hits a mandatory high-risk
article the overall **auditor opinion** becomes a *disclaimer of opinion*. The
report's `auditor_opinion.opinion_type` is one of *unqualified*, *qualified*,
*adverse*, or *disclaimer_of_opinion*.

### KPI scores

| Score | What it means | Good value |
|-------|--------------|-----------|
| **Intake completeness (KPI 0)** | How much required documentation you provided | ≥ 0.80 |
| **Evidence completeness (KPI 1)** | How thoroughly the agents found supporting evidence | ≥ 0.80 |
| **Regulatory coverage (KPI 2)** | % of relevant EU AI Act articles assessed | ≥ 90% |

### Downloads

- **Client brief (Markdown)** — start here. The same result as the PDF, written
  in plain language and requirement by requirement: what your submission
  declared, what the evidence actually showed, which article the gap falls
  under, and what to do about it. Written to
  `data/customer/<company>/<engagement>_client_report.md` at the end of every
  run. It explains the audit; it never restates a verdict differently from the
  PDF, and where the two are read differently the PDF and its evidence govern.
- **Audit Report (PDF)** — the formal report, addressed to a conformity
  assessor: cover with verdict and
  KPIs, executive summary, auditor opinion, risk classification, compliance
  matrix, findings by severity, governance maturity, explainability & fairness
  and security & robustness evidence, and the documentation inventory. It is
  also written to `data/customer/<company>/<engagement>_audit_report.pdf` at
  the end of every run.
- **T17 Compliance Matrix (JSON)** — each article → verdict, with a per-article
  rationale and evidence links.
- **T18 Audit Report (JSON)** — full report: executive summary, findings,
  remediation roadmap.
- **Full audit state (JSON)** — the complete machine-readable result; also at
  `GET /api/v1/engagements/{id}/audit-state`.

**Regenerate every company's PDF offline** (no LLM, no API keys needed):

```bash
python -m aaa report --all               # every folder under data/customer/
python -m aaa report --company finclear_gmbh
```

**Rewrite the client brief** from a saved audit state — for runs that finished
before the brief existed, or to reword one without re-auditing. Unlike `report`
this calls the model, so it needs `PROVIDER` and the matching API key. It reads
the verdicts and findings as they were recorded and cannot change them:

```bash
python -m aaa brief --all                # every folder under data/customer/
python -m aaa brief --company finclear_gmbh
```

### The results dashboard

The last step is a dashboard addressed to the customer, not to an auditor.
Reading order is theirs: the conclusion first, then the numbers behind it, then
the documents, then the detail.

- **The verdict masthead** states the outcome as a sentence — "We found gaps you
  will need to close", "Your system met every requirement we assessed" — beside
  an **article-conformity gauge** (0–100, weighted PASS percentage over
  applicable articles). Your engagement reference, completion date, risk tier
  and Annex III scope sit under it as chips.
- **Four statistics**: conformity score, requirements met (out of those that
  apply — articles marked not-applicable are excluded from both halves of the
  fraction), how many need attention, and how complete the documentation you
  supplied was.
- **Your documents** — two PDFs and nothing else (see below).
- **The auditor's opinion**, quoted verbatim.
- **What we checked** — every article grouped by outcome, worst first, each one
  headed by its *subject* ("Checking datasets for bias") with the article
  reference underneath. Not-met and could-not-be-checked groups open by default.
- **What to do next** — the remediation roadmap as a ranked to-do list with
  deadlines and severity.

Nothing on this page names an artefact, a phase, or a template id.

### What the customer downloads

Exactly two files, both PDFs:

| Document | Downloads as | What it is |
|----------|--------------|------------|
| **Your audit report** | `<id>_plain_language_report.pdf` | The plain-language brief (Agent 14), rendered to PDF. Written to be read without an auditor present. Offered first. |
| **Formal conformity report** | `<id>_audit_report.pdf` | The signed report with evidence references, for the technical file or a notified body. Same name it carries in `data/customer/<company>/`. |

T17, T18, the HITL packet and the raw AuditState are **not** offered here. A
customer handed `eng-06_T18.json` has been handed our filing system and asked to
work out which file is their report.

If the run is **degraded** (`run_integrity.suitable_for_handoff` is false), the
downloads are withheld entirely and the customer is told the audit did not
finish cleanly and will be re-run. The files still exist — in the admin console,
with `_DEGRADED` in every filename.

### The admin console

An **⚙ Admin console** button sits at the top left of the dashboard. It swaps
the whole view (`st.session_state["view"] = "admin"`) for the auditor-facing
surface, under an ink masthead reading *Internal review — not client-facing* so
nobody mistakes it for something a client is looking at. Three tabs:

- **Review & sign-off** — the HITL review packet, the `finalize_hitl` command,
  and the run record (run id, code revision, artefact count, signature state,
  per-phase status).
- **Artefacts** — both client PDFs plus T17, T18, the client-brief Markdown
  source, and the full AuditState.
- **Findings & evidence** — the raw article/verdict matrix with finding counts,
  findings grouped by severity, the Art. 13 / Art. 15 evidence status, and the
  Annex IV documentation inventory.

**← Back to the client dashboard** returns.

### Findings

Findings carry a severity chip (material = red, possibly-material = amber,
observation = indigo) and the articles each touches — for a high-risk
classifier, this is where a **material** fairness failure would appear.
Material findings render open; lower severities and positive findings sit in
collapsible sections. They live in the admin console's *Findings & evidence*
tab; what the customer sees on their dashboard is the article breakdown and the
remediation roadmap.

### Human review (provisional reports)

If the auditor escalated any artefact, the customer's dashboard says so in one
calm note — *Provisional — with a senior auditor for sign-off*, "nothing is
needed from you" — and nothing else changes for them.

The packet itself is in the admin console, under **Review & sign-off**. To
finalize:

1. Download `<id>_hitl_review.json` and set each case's `human_decision` to
   `accept`, `uphold_escalation`, or `override` (with
   `human_suggested_verdict`); add a short `human_rationale`.
2. Save, then run `python -m scripts.finalize_hitl <engagement_id>`.

This applies your decisions, recomputes the matrix and KPIs, and writes the
**FINAL** T17/T18.

---

## Part 10 — Quick reference

### Commands you'll use most

| What you want | Command |
|---------------|---------|
| One-time setup | `python3.12 -m scripts.setup --no-docker --no-migrate` |
| Activate environment (Mac/Linux) | `source .venv/bin/activate` |
| Activate environment (Windows) | `.venv\Scripts\activate` |
| **Start everything** | `make start` (or `python -m aaa`) |
| Start just the UI | `aaa ui` |
| Start just the API | `aaa api` |
| Headless audit of a fixture | `aaa audit --engagement-id demo` |
| Run a bundled mock case | `python -m scripts.run_mock_case 01_finclear_gmbh` |
| Finalize a provisional report | `python -m scripts.finalize_hitl <engagement_id>` |
| Regenerate every company's PDF | `python -m aaa report --all` |
| Start the observability dashboard | `make obs` (Grafana at `:3002`) |
| Stop the observability dashboard | `make obs-down` |
| **Stop** a running command | `Ctrl + C` |
| Stop Docker (keeps data) | `docker compose down` |
| Run tests | `pytest -q` |
| Build API docs | `make -C docs html` |

### Important files and folders

| Path | What it is |
|------|-----------|
| `.env` | Your configuration — launch plan and API keys |
| `aaa/launcher/` | The one-command launcher (`python -m aaa`) |
| `aaa/ui/app.py` | The Streamlit wizard |
| `aaa/api/main.py` | The FastAPI application |
| `aaa/data/` | The persistence layer |
| `scripts/fixtures/uci_german_credit/` | Sample audit data |
| `data/regulatory_corpus/` | Source documents for the regulatory corpus |
| `logs/audit/llm_audit.jsonl` | Per-call LLM audit trail |
| `docs/` | Sphinx API documentation source |
| `SETUP.md` | Technical quick-start |
| `ARCHITECTURE.md` | How the system is designed |

### The `.env` settings that matter most

| Setting | What it does | Typical value |
|---------|-------------|---------------|
| `AAA_LAUNCH_API` / `AAA_LAUNCH_UI` | Which surfaces `make start` brings up | `true` |
| `AAA_LAUNCH_DOCKER` / `AAA_LAUNCH_MIGRATE` | Whether infra + migrations run on start | `auto` |
| `OPENAI_API_KEY` | Enables real LLM analysis | `sk-...` (blank for the demo) |
| `CGSA_FIXTURE_DIR` | Where CGSA assessments are looked up, in order (path-separated) | `mock:scripts/fixtures/cgsa` |
| `AAA_CGSA_FIXTURE_DIR` | Overrides the above outright — for re-running a case against a real S5 export held outside the repo | *(unset)* |
| `AAA_LOG_LEVEL` | How much log output you see | `WARNING` (`INFO` to debug) |
| `AAA_DATA_DIR` | Where persisted engagement JSON is written | `data` |
| `EMBEDDINGS_CLIENT_DOCS` | Where the customer's uploaded files are embedded (Part 5) | `openai` (`local` keeps them on your machine) |
| `EMBEDDINGS_REGULATORY` | Where legal-corpus queries are embedded — changing it needs a corpus rebuild | `openai` |
| `EMBEDDINGS_EVIDENCE` | Where evidence re-ranking is embedded | `openai` |
| `EMBEDDINGS_LOCAL_MODEL` | Which local model `local` uses — no default, you must choose | `all-MiniLM-L6-v2` |
