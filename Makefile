# AAA — Autonomous AI Auditor: Unified Makefile
# Python 3.12 REQUIRED.

PYTHON := .venv/bin/python
PIP    := .venv/bin/pip
FIXTURE_INTAKE_DIR := scripts/fixtures/uci_german_credit
FIXTURE_CGSA_DIR := scripts/fixtures/cgsa
FIXTURE_RUN := CGSA_FIXTURE_DIR=$(FIXTURE_CGSA_DIR) $(PYTHON) -m aaa.cli run --intake-dir $(FIXTURE_INTAKE_DIR) --cgsa-fixture-dir $(FIXTURE_CGSA_DIR)

.PHONY: start bootstrap bootstrap-demo venv install up down obs obs-down ui lint test coverage \
        intake-validate intake-demo \
        m3-linear m4-full m5-case1 m5-case2 m6-case3 m6-case4 \
        report-german demo deploy-staging deploy-prod

# One command to run everything (infra + API + UI), driven by .env:
start: ; $(PYTHON) -m aaa

# Fresh clone → venv + deps → .env → bundles → Docker (core + obs + ui) →
# corpus embedded through OpenRouter → API + UI → one browser window with
# every service dashboard in a tab and the Mariposa wizard filled and running.
# Needs mariposa.zip and corpus.zip in the repo root and one OpenRouter key.
bootstrap:      ; python3.12 bootstrap.py $(BOOTSTRAP_ARGS)
# Same path without spending: a local stub answers embeddings and refuses chat.
bootstrap-demo: ; python3.12 bootstrap.py --mock-llm $(BOOTSTRAP_ARGS)

venv:
	python3.12 -m venv .venv

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	.venv/bin/pre-commit install

up:       ; docker compose up -d && $(PYTHON) -m alembic upgrade head
down:     ; docker compose --profile obs --profile ui down
obs:      ; docker compose --profile obs up -d
                # Grafana http://localhost:3002 (admin/$$GF_SECURITY_ADMIN_PASSWORD, default admin)
obs-down: ; docker compose --profile obs stop prometheus loki alloy grafana
ui:       ; docker compose --profile ui up -d
                # pgweb http://127.0.0.1:8081 (Postgres), redis-commander http://127.0.0.1:8082 (Valkey)
lint:     ; .venv/bin/ruff check . && .venv/bin/pylint aaa scripts && .venv/bin/pyright aaa
test:     ; $(PYTHON) -m pytest -q
coverage: ; $(PYTHON) -m pytest --cov=aaa --cov-report=term-missing --cov-fail-under=70

# --- intake targets ---
intake-validate:; $(FIXTURE_RUN) --engagement-id eng-validate-001
                # Validation smoke using the UCI German Credit fixture bundle.
intake-demo:    ; $(FIXTURE_RUN) --engagement-id eng-demo-001
                # Full fixture demo: IntakeValidator → Orchestrator → final verdict.

# --- exposé milestones ---
m3-linear:    ; $(FIXTURE_RUN) --engagement-id eng-m3-001
m4-full:      ; $(FIXTURE_RUN) --engagement-id eng-m4-001
m5-case1:     ; $(FIXTURE_RUN) --engagement-id eng-m5-case1
m5-case2:     ; $(FIXTURE_RUN) --engagement-id eng-m5-case2
m6-case3:     ; $(FIXTURE_RUN) --engagement-id eng-m6-case3
m6-case4:     ; $(FIXTURE_RUN) --engagement-id eng-m6-case4

# --- demo + deploy ---
report-german:; $(FIXTURE_RUN) --engagement-id eng-uci-german-credit-001 --output-file out/eng-uci-german-credit-001.json
demo:         ; .venv/bin/streamlit run aaa/ui/app.py
deploy-staging:; tofu -chdir=infra/tofu workspace select staging && tofu -chdir=infra/tofu apply -auto-approve
deploy-prod:  ; tofu -chdir=infra/tofu workspace select prod    && tofu -chdir=infra/tofu apply
