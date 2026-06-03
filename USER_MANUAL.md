# User Manual — EU AI Act Compliance Audit System

**Who this is for:** Someone who has cloned this repository and wants to run the system.
No prior experience with Python virtual environments, Docker, or AI frameworks is assumed.
Every step is spelled out exactly.

---

## What does this system do?

In plain English: you upload your AI system's technical documents, answer 8 short questions,
and this system automatically checks whether your AI system complies with the EU AI Act.
It reads your documents, fills in a compliance form, runs 13 AI agents behind the scenes,
and gives you a final verdict: **PASS**, **PASS WITH OBSERVATIONS**, or **FAIL** — along
with a detailed report you can download.

---

## Two ways to run it

| Mode | What it needs | When to use it |
|------|--------------|----------------|
| **Offline mode** | Just Python + the repo | Learning the system, testing, demo |
| **Online mode** | Python + Docker + OpenAI API key | Real compliance audits with AI analysis |

**If this is your first time — start with offline mode.** It works without any API keys,
without Docker, and gives you the full wizard experience. Online mode adds the AI agents
that actually read your documents and write the report.

---

## Part 1 — Before you start: install the prerequisites

### Step 1.1 — Check if you already have Python 3.12

Open your Terminal (Mac/Linux) or Command Prompt (Windows) and type:

```
python3 --version
```

You should see something like `Python 3.12.x`. If you see `Python 3.11` or lower, or an
error, follow Step 1.2. If you already have Python 3.12, skip to Step 1.3.

> **What is the Terminal?** On a Mac: press `Cmd + Space`, type "Terminal", press Enter.
> On Windows: press `Win + R`, type `cmd`, press Enter. On Linux: `Ctrl + Alt + T`.

### Step 1.2 — Install Python 3.12

**Mac:**
1. Go to `https://www.python.org/downloads/`
2. Click **Download Python 3.12.x** (the big yellow button)
3. Open the downloaded file and follow the installer
4. When done, close and reopen your Terminal, then check again: `python3.12 --version`

**Windows:**
1. Go to `https://www.python.org/downloads/`
2. Click **Download Python 3.12.x**
3. Run the installer. **Important:** Check the box that says "Add Python to PATH" on the
   first screen before clicking Install
4. Close and reopen Command Prompt, then check: `python --version`

**Linux (Ubuntu/Debian):**
```
sudo apt update
sudo apt install python3.12 python3.12-venv
```

### Step 1.3 — Make sure you're in the right folder

In your Terminal, navigate to where you cloned the repository. The folder should be named
`UAGF_TAM_AAA` (or whatever you named it). Type:

```
cd /path/to/UAGF_TAM_AAA
```

Replace `/path/to/UAGF_TAM_AAA` with the actual location. For example:
- Mac: `cd ~/Documents/Thesis/UAGF_TAM_AAA`
- Windows: `cd C:\Users\YourName\Documents\UAGF_TAM_AAA`

To confirm you're in the right place, type `ls` (Mac/Linux) or `dir` (Windows).
You should see files like `README.md`, `SETUP.md`, `requirements.txt`, and folders like `aaa/`, `data/`, `scripts/`.

---

## Part 2 — Set up the system

You have two options: **automatic setup** (one command does everything) or **manual setup**
(step by step, useful if automatic fails).

---

### Option A — Automatic setup (recommended for first-timers)

This single command installs everything for offline use:

```
python3.12 scripts/setup.py --no-docker --no-migrate
```

> **What does `--no-docker` and `--no-migrate` mean?** Those flags skip the Docker services
> and database setup — you don't need them for offline mode. You can add them later for
> online mode.

**What you will see on screen** (this takes 2–5 minutes):

```
[1/7] Verify Python version
  ✓ Python 3.12.x (>= 3.12)

[2/7] Create virtualenv
  ✓ created .venv/

[3/7] Install Python dependencies
  $ .venv/bin/python -m pip install --upgrade pip
  $ .venv/bin/python -m pip install -r requirements-dev.txt
  ... (many lines of package downloads) ...
  ✓ installed requirements-dev.txt

[4/7] Copy .env.example -> .env
  ✓ created .env from .env.example (edit it before running with real secrets)

[5/7] Start docker compose stack
  ! --no-docker: skipping docker compose up -d

[6/7] Apply alembic migrations
  ! --no-migrate: skipping alembic upgrade head

[7/7] Run offline smoke test
  ... (test output) ...
  ✓ smoke test passed

✓ Setup complete.

Next steps:
  1. Activate the venv:  . .venv/bin/activate
  ...
```

If you see the `✓ Setup complete.` line, the setup worked. Move to Part 3.

**If the setup fails** with a red `✗` message, use manual setup below.

---

### Option B — Manual setup (step by step)

Do these steps one at a time. Each step must succeed before moving to the next.

**Step B.1 — Create a virtual environment**

```
python3.12 -m venv .venv
```

> **What is a virtual environment?** It's an isolated box for this project's Python packages,
> so they don't interfere with other Python projects on your computer. Think of it as a
> dedicated drawer just for this project.

You should see nothing (no output = success for this command).

**Step B.2 — Activate the virtual environment**

Mac/Linux:
```
source .venv/bin/activate
```

Windows:
```
.venv\Scripts\activate
```

After this, your Terminal prompt changes to show `(.venv)` at the start, like:
```
(.venv) user@machine UAGF_TAM_AAA %
```

This tells you the virtual environment is active. You must do this every time you open a
new Terminal to work with this project.

**Step B.3 — Upgrade pip (the package installer)**

```
pip install --upgrade pip
```

You should see `Successfully installed pip-XX.X`.

**Step B.4 — Install project dependencies**

```
pip install -r requirements-dev.txt
```

This downloads and installs all the Python libraries the project needs. It takes 2–5 minutes.
You will see many lines scrolling — this is normal. Wait for the `Successfully installed ...` line at the end.

**Step B.5 — Create your configuration file**

```
cp .env.example .env
```

Windows:
```
copy .env.example .env
```

This creates a file called `.env` that holds your configuration. You will edit it in Part 4.

**Step B.6 — Verify the installation**

```
AAA_OFFLINE_MODE=true pytest -m "not e2e" --no-cov -q
```

Windows (Command Prompt):
```
set AAA_OFFLINE_MODE=true && pytest -m "not e2e" --no-cov -q
```

You should see output ending with something like:
```
... passed in X.Xs
```

If tests pass, the installation is working. If they fail, see Part 7 (Troubleshooting).

---

## Part 3 — Activate the virtual environment (do this every session)

Every time you open a new Terminal to work with this project, you must activate the
virtual environment first. Without it, the commands will not work.

Mac/Linux:
```
source .venv/bin/activate
```

Windows:
```
.venv\Scripts\activate
```

Your prompt should start with `(.venv)`. If it does, you're ready.

---

## Part 4 — Configure your .env file

The `.env` file controls how the system behaves. Open it in any text editor (Notepad,
TextEdit, VS Code, etc.). It was created in Step B.5 or by the automatic setup.

The file has many lines. Most of them you can ignore. Here are the only ones you need
to change depending on your mode:

### For offline mode (no changes needed)

The default `.env` file already works for offline mode. The key line is:

```
AAA_OFFLINE_MODE=false
```

For offline mode, change it to:

```
AAA_OFFLINE_MODE=true
```

Or you can just pass it as a command-line prefix (shown in Part 5) without editing the file.

### For online mode (you need an OpenAI API key)

Find this line in `.env`:

```
OPENAI_API_KEY=sk-...
```

Replace `sk-...` with your actual OpenAI API key. To get one:
1. Go to `https://platform.openai.com/api-keys`
2. Sign in (or create an account)
3. Click **Create new secret key**
4. Copy the key (it starts with `sk-`) — you only see it once, so copy it immediately
5. Paste it into `.env` replacing `sk-...`

Also change offline mode to false:

```
AAA_OFFLINE_MODE=false
```

Save and close the file.

---

## Part 5 — Running in offline mode (no API key needed)

Offline mode uses pre-built fixture data to demonstrate the full pipeline. The AI agents
run in rule-based mode (no LLM calls). The wizard works fully — you can upload documents
and fill the form — but the DocIntelligenceAgent will not auto-read your documents
(it needs Qdrant for that, which requires Docker).

### Method 1 — Streamlit wizard (easiest, point-and-click)

Make sure the virtual environment is active (you see `(.venv)` in your prompt), then:

**Mac/Linux:**
```
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

**Windows (Command Prompt):**
```
set AAA_OFFLINE_MODE=true
set CGSA_FIXTURE_DIR=scripts/fixtures/cgsa
streamlit run aaa/ui/app.py
```

**What you should see in the Terminal:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Your browser should open automatically. If not, open your browser and go to:
```
http://localhost:8501
```

**Walking through the 5-step wizard:**

**Step 0 — Start:**
- You see a screen titled "EU AI Act Compliance Audit" with an explanation
- There is a text box for **Engagement ID** — this is just a name for this audit run
- The system fills in a random ID like `eng-a1b2c3d4` for you. You can change it or leave it
- Click the blue **Start Audit** button

**Step 1 — Upload Documents:**
- You see three upload zones
- **Technical documents**: Upload any PDF, Word doc, or text file that describes your AI system (model card, data sheet, technical specification, risk assessment). If you have none, you can skip and click Continue
- **Model artefact** (optional): Upload your trained model file if you have one
- **Datasets** (optional): Upload training or evaluation dataset files
- In offline mode: the system stores your files but cannot read them automatically (that requires online mode)
- Click **Continue without documents** (if you have no files) or **Analyse Documents** (if you uploaded files)

**Step 2 — Quick Questions:**
- You see 8 questions about your AI system
- Answer each one honestly. If unsure, pick the closest option
  - Question 1: Are you the company that built the AI (Provider) or are you using someone else's AI (Deployer)?
  - Question 2: Who uses this system? (B2B = businesses, B2C = consumers, Public Sector = government, Internal = just your own company)
  - Question 3: Does the system handle personal information like names, emails, or locations?
  - Question 4: (Shows only if Q3 = Yes) Does it handle sensitive data like health records or biometric data?
  - Question 5: Is this a general-purpose AI like a large language model (ChatGPT-style)?
  - Question 6: Does this system fall under any of the 8 high-risk categories in the EU AI Act? (e.g. credit scoring = category 5)
  - Question 7: Are you choosing to have a third party verify your compliance voluntarily?
  - Question 8: Where is the system used? Select the EU territories that apply
- Click **Continue**

**Step 3 — Review & Confirm:**
- You see two expandable sections: **Stage A — System Declaration** and **Stage B — Technical Documentation**
- In offline mode, all fields are empty (no auto-fill). You need to fill them in
- Each field has a description underneath it explaining exactly what to put
- Fields with `*` are required. An amber warning box appears on empty required fields
- Watch the **Intake completeness** score at the top — it must reach **80%** or higher before you can run the audit
- The key required Stage A fields: Legal provider name, System name, Version, Intended purpose, AI modality, Risk tier, Annex III categories, Deployment context
- The key required Stage B fields: General description, Model type, Design process, Training data description, Data governance measures, Monitoring measures, Logging capabilities, Performance metrics, Lifecycle changes log, Standards applied
- Fill them in, watching the completeness score rise
- When the score reaches 80% and the scope gate shows "in scope", the **Confirm & Run Audit** button becomes active
- Click **Confirm & Run Audit**

**Step 4 — Results:**
- A spinner appears while the audit runs ("Running IntakeValidator → Orchestrator…")
- In offline mode this takes 10–60 seconds
- When done, you see a green/orange/red banner with the final verdict
- Three KPI scores are shown: Intake completeness, Evidence completeness, Regulatory coverage
- Scroll down to see the Compliance Matrix and download buttons

**To stop the Streamlit server:**

1. Go back to the Terminal window where Streamlit is running
2. Press `Ctrl + C` (hold the Control key and press C at the same time)
3. You should see the server shut down and your normal Terminal prompt return

> **Nothing seems to happen when I press Ctrl+C?** Press it once more. If still stuck,
> close the Terminal window entirely — the server stops when the window closes.

---

### Method 2 — Command Line (fastest, uses sample data)

This runs the audit using the pre-built sample data in `scripts/fixtures/uci_german_credit/`.
No form-filling required.

Make sure the virtual environment is active, then:

**Mac/Linux:**
```
AAA_OFFLINE_MODE=true \
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
python -m aaa.cli run \
  --engagement-id eng-demo-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline
```

**Windows:**
```
set AAA_OFFLINE_MODE=true
set CGSA_FIXTURE_DIR=scripts/fixtures/cgsa
python -m aaa.cli run --engagement-id eng-demo-001 --intake-dir scripts/fixtures/uci_german_credit --cgsa-fixture-dir scripts/fixtures/cgsa --offline
```

Or with the shortcut:
```
make intake-demo
```

**What you should see:**
```
Running IntakeValidator...
Running Orchestrator (Phase 1–6)...
...
{
  "final_verdict": "PASS_WITH_OBSERVATIONS",
  "intake_completeness_score": 0.87,
  "completeness_score": 0.82,
  "regulatory_coverage_pct": 74.3,
  ...
}
```

The CLI command finishes on its own — there is nothing to stop. Once the JSON output
appears and you see your Terminal prompt again, the run is complete.

If you want to stop it mid-run, press `Ctrl + C`.

---

## Part 6 — Running in online mode (requires API key + Docker)

Online mode enables the full AI pipeline:
- The DocIntelligenceAgent reads your uploaded documents and auto-fills the form
- All 13 AI agents run with real LLM calls
- The Regulatory RAG agent searches the full EU AI Act, GDPR, and ISO standards corpus
- The final report is generated with real AI-written analysis

### Step 6.1 — Install Docker Desktop (if you do not have it)

1. Go to `https://www.docker.com/products/docker-desktop/`
2. Click the download button for your operating system (Mac/Windows/Linux)
3. Install it and start Docker Desktop
4. Wait until you see the Docker whale icon in your menu bar / taskbar showing "Docker Desktop is running"

To verify Docker is working:
```
docker --version
```

You should see something like `Docker version 27.x.x`.

### Step 6.2 — Add your OpenAI API key to .env

Open `.env` in a text editor and set:

```
OPENAI_API_KEY=sk-your-actual-key-here
AAA_OFFLINE_MODE=false
```

Save the file.

### Step 6.3 — Start the required background services

This starts the database and vector search services the system needs:

```
docker compose up -d
```

> **What does `-d` mean?** It means "run in the background" (detached). The services keep
> running even after you close the Terminal.

Wait about 30 seconds. To check that they started correctly:

```
docker compose ps
```

You should see these services all showing `healthy` or `running` (not `exiting`):

| Service | What it does |
|---------|-------------|
| `postgres` | Stores engagement data |
| `qdrant` | Vector search for document retrieval |
| `minio` | Stores uploaded files and audit artefacts |
| `valkey` | Background job queue |

If any service shows `exiting`, see Part 7 Troubleshooting.

### Step 6.4 — Apply database migrations (first time only)

```
python -m alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade ...
```

You only need to do this once after setup, or after pulling new code changes.

### Step 6.5 — Ingest the regulatory corpus (first time only, takes ~5 minutes)

This loads the EU AI Act, GDPR, ISO 42001, ISAE 3000, and ISO 19011 into the vector search
database so the AI agents can look up regulatory requirements:

First, do a dry run to confirm everything is ready:
```
python3.12 scripts/ingest_regulatory_corpus.py --dry-run -v
```

You should see something like:
```
[dry-run] EU AI Act: 339 chunks
[dry-run] GDPR: 288 chunks
[dry-run] ISO/IEC 42001: 88 chunks
[dry-run] ISAE 3000: 411 chunks
[dry-run] ISO 19011: 74 chunks
[dry-run] Total: 1200 chunks
```

Then run the actual ingestion:
```
python3.12 scripts/ingest_regulatory_corpus.py \
  --corpus data/regulatory_corpus \
  --checker data/eu_ai_act_compliance_checker.json \
  --collection regulatory_corpus \
  --obligations-collection obligations_index
```

Windows:
```
python scripts/ingest_regulatory_corpus.py --corpus data/regulatory_corpus --checker data/eu_ai_act_compliance_checker.json --collection regulatory_corpus --obligations-collection obligations_index
```

This is a one-time step. The script is safe to re-run — it skips chunks it already embedded.

### Step 6.6 — Run the Streamlit wizard in online mode

**Mac/Linux:**
```
CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \
streamlit run aaa/ui/app.py
```

**Windows:**
```
set CGSA_FIXTURE_DIR=scripts/fixtures/cgsa
streamlit run aaa/ui/app.py
```

Notice: there is no `AAA_OFFLINE_MODE=true` prefix this time. The system uses the value
from your `.env` file, which you set to `false` in Step 6.2.

**What is different in online mode vs offline mode:**

The wizard looks identical, but in Step 1 (Upload Documents):
- When you click **Analyse Documents**, the system actually reads your files
- The DocIntelligenceAgent uses AI to extract information from your documents
- In Step 3 (Review & Confirm), fields that were extracted from your documents will show a caption like:
  `Auto-filled from your-document.pdf · 87% high confidence`
- Fields not found in your documents still show the amber "please fill in manually" warning

In Step 4 (Results):
- The audit takes longer (1–5 minutes depending on document size)
- The compliance matrix contains AI-generated analysis, not just rule-based checks
- The download links produce a real AI-written audit report

---

### Step 6.7 — Stopping everything (online mode)

When you are done working, stop each running component in this order:

**1. Stop the Streamlit server**

Go to the Terminal running Streamlit and press `Ctrl + C`.
You should see:
```
  Stopping...
```
and your prompt returns. The browser tab will show "This site can't be reached" — that is
correct, it means Streamlit has stopped.

**2. Stop the Docker services**

In any Terminal (the virtual environment does not need to be active for this):

```
docker compose down
```

You should see each service listed as it stops:
```
[+] Running 5/5
 ✔ Container uagf_tam_aaa-qdrant-1    Stopped
 ✔ Container uagf_tam_aaa-minio-1     Stopped
 ✔ Container uagf_tam_aaa-valkey-1    Stopped
 ✔ Container uagf_tam_aaa-postgres-1  Stopped
 ✔ Network uagf_tam_aaa_default       Removed
```

> **Does stopping Docker delete my data?** No. `docker compose down` stops the containers
> but keeps all your data volumes. Your regulatory corpus, uploaded files, and engagement
> results are preserved. Only `docker compose down -v` (with the `-v` flag) deletes volumes —
> do not add `-v` unless you want a completely fresh start.

**3. Deactivate the virtual environment (optional)**

If you want to cleanly exit the virtual environment in your Terminal:

```
deactivate
```

The `(.venv)` prefix disappears from your prompt. You can always reactivate it later with
`source .venv/bin/activate` (Mac/Linux) or `.venv\Scripts\activate` (Windows).

**Summary — in 3 commands:**

```
Ctrl + C                 ← stops Streamlit (in the Streamlit terminal)
docker compose down      ← stops all background services
deactivate               ← exits the virtual environment
```

---

## Part 7 — Troubleshooting

### "python3.12: command not found" or "python: command not found"

You need to install Python 3.12. See Part 1, Step 1.2.

On Mac, you may have Python 3.12 installed but need to use the exact name:
```
python3.12 --version
```

### "ModuleNotFoundError: No module named 'streamlit'" (or any other module)

The virtual environment is not active. Do this:
```
source .venv/bin/activate
```
Then retry your command.

### "No module named 'aaa'"

Same cause as above — the virtual environment is not active. Also make sure you are in
the repository root folder (the one containing `aaa/`, `requirements.txt`, etc.).

### "Streamlit is not installed"

Run:
```
pip install streamlit
```

Or reinstall all packages:
```
pip install -r requirements-dev.txt
```

### The Streamlit page does not open in browser

Open your browser manually and go to: `http://localhost:8501`

### "Address already in use: port 8501"

Streamlit is already running. Either close the other Terminal that has it running, or
run on a different port:
```
streamlit run aaa/ui/app.py --server.port 8502
```

Then open: `http://localhost:8502`

### "Intake completeness is X% — fill in more fields to reach the 0.80 gate"

You need to fill in more fields in Step 3. The most common missing fields are:
- General system description (Stage B) — needs at least 50 characters
- Intended purpose (Stage A) — needs at least 20 characters
- Performance metrics (Stage B) — must be valid JSON like `{"accuracy": 0.78}`
- Training data description (Stage B) — needs at least 30 characters

Keep filling fields until the green progress bar at the top reaches 80%.

### Docker services not starting ("exiting" status)

Check the logs to see why:
```
docker compose logs postgres
docker compose logs qdrant
```

Common fixes:
1. Port conflict — another program is using the same port. Edit `.env` to change the port number
2. Disk space — Docker needs free space. Delete old Docker images: `docker system prune`
3. Permission error on Mac — restart Docker Desktop from the menu bar icon

Restart services:
```
docker compose down
docker compose up -d
```

### "OpenAI API error" or "AuthenticationError"

Your API key in `.env` is missing or wrong. Check that:
1. The key starts with `sk-`
2. There are no spaces before or after it
3. You have credit on your OpenAI account at `https://platform.openai.com/usage`

### The audit runs but gives "FAIL" with no explanation

In offline mode, agents run in rule-based mode and may return conservative results with
incomplete evidence. This is expected. Switch to online mode with real documents for
meaningful results.

### Resetting everything to start fresh

To completely start over (removes the virtual environment and .env):
```
rm -rf .venv .env
```

Windows:
```
rmdir /s /q .venv
del .env
```

Then go back to Part 2 and set up again.

---

## Part 8 — Understanding the output

When the audit finishes, you see:

### Final verdict

| Verdict | What it means |
|---------|--------------|
| **PASS** | All critical EU AI Act requirements are met. Full evidence provided. Regulatory coverage ≥ 90%. |
| **PASS WITH OBSERVATIONS** | Mostly compliant, but some gaps exist (e.g. regulatory coverage 70–89%). Minor improvements recommended. |
| **FAIL** | One or more critical requirements are not met, or intake completeness < 80%, or critical articles are unaddressed. |

### KPI scores

| Score | What it means | Good value |
|-------|--------------|-----------|
| **Intake completeness (KPI 0)** | How much of the required documentation you provided | ≥ 0.80 |
| **Evidence completeness (KPI 1)** | How thoroughly the audit agents found supporting evidence | ≥ 0.80 |
| **Regulatory coverage (KPI 2)** | What % of relevant EU AI Act articles were assessed | ≥ 90% |

### Downloads

- **T17 Compliance Matrix (JSON)** — A table mapping each EU AI Act article to a verdict (PASS/FAIL/N/A) with evidence links
- **T18 Audit Report (JSON)** — The full audit report including executive summary, findings, and remediation roadmap
- **Audit Report (PDF)** — The same report as a formatted PDF (available when the Report Architect agent successfully renders it)

### Remediation checklist

If the verdict is FAIL or PASS WITH OBSERVATIONS, a **Remediation Checklist** expander
shows the specific problems found, listed by article number and severity. Each item
identifies what is missing and what action is needed.

---

## Part 9 — Quick reference

### Commands you will use most often

| What you want to do | Command |
|---------------------|---------|
| Activate virtual environment (Mac/Linux) | `source .venv/bin/activate` |
| Activate virtual environment (Windows) | `.venv\Scripts\activate` |
| **Deactivate** virtual environment | `deactivate` |
| Start Streamlit wizard (offline) | `AAA_OFFLINE_MODE=true CGSA_FIXTURE_DIR=scripts/fixtures/cgsa streamlit run aaa/ui/app.py` |
| **Stop Streamlit** | `Ctrl + C` in the Terminal running Streamlit |
| Start Streamlit wizard (online) | `CGSA_FIXTURE_DIR=scripts/fixtures/cgsa streamlit run aaa/ui/app.py` |
| Run CLI demo with sample data | `make intake-demo` |
| **Stop CLI** mid-run | `Ctrl + C` |
| Start Docker services | `docker compose up -d` |
| **Stop Docker** services (keeps data) | `docker compose down` |
| **Stop Docker** + delete all data | `docker compose down -v` |
| Check Docker service health | `docker compose ps` |
| Reinstall packages | `pip install -r requirements-dev.txt` |
| Run tests | `AAA_OFFLINE_MODE=true pytest -m "not e2e" -q` |

### Important files and folders

| Path | What it is |
|------|-----------|
| `.env` | Your configuration file — API keys and mode settings go here |
| `aaa/ui/app.py` | The Streamlit wizard |
| `scripts/fixtures/uci_german_credit/` | Sample audit data for testing |
| `data/eu_ai_act_compliance_checker.json` | The EU AI Act questionnaire used for scoping |
| `data/regulatory_corpus/` | Source documents for the regulatory corpus (EU AI Act, GDPR, etc.) |
| `requirements.txt` | Full ML/production dependencies |
| `requirements-dev.txt` | Development dependencies (lighter, faster to install) |
| `SETUP.md` | Technical quick-start guide |
| `ARCHITECTURE.md` | How the system is designed |

### The .env settings that matter most

| Setting | What it does | Offline value | Online value |
|---------|-------------|---------------|--------------|
| `AAA_OFFLINE_MODE` | Disables all external calls | `true` | `false` |
| `OPENAI_API_KEY` | Your OpenAI key for AI agents | not needed | `sk-your-key` |
| `CGSA_FIXTURE_DIR` | Where the sample CGSA data lives | `scripts/fixtures/cgsa` | `scripts/fixtures/cgsa` |
| `AAA_LOG_LEVEL` | How much log output you see | `WARNING` | `INFO` for debugging |
