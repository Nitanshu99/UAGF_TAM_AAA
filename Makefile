# AAA — Autonomous AI Auditor: Unified Makefile
# Python 3.12 REQUIRED.

PYTHON := .venv/bin/python
PIP    := .venv/bin/pip
FIXTURE_INTAKE_DIR := scripts/fixtures/uci_german_credit
FIXTURE_CGSA_DIR := scripts/fixtures/cgsa
OFFLINE_RUN := AAA_OFFLINE_MODE=true CGSA_FIXTURE_DIR=$(FIXTURE_CGSA_DIR) $(PYTHON) -m aaa.cli run --intake-dir $(FIXTURE_INTAKE_DIR) --cgsa-fixture-dir $(FIXTURE_CGSA_DIR) --offline

.PHONY: venv install up down lint test coverage \
        intake-validate intake-demo \
        m3-linear m4-full m5-case1 m5-case2 m6-case3 m6-case4 \
        report-german demo deploy-staging deploy-prod

venv:
	python3.12 -m venv .venv

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	.venv/bin/pre-commit install

up:       ; docker compose up -d && $(PYTHON) -m alembic upgrade head
down:     ; docker compose down
lint:     ; .venv/bin/ruff check . && .venv/bin/mypy aaa/
test:     ; $(PYTHON) -m pytest -q
coverage: ; $(PYTHON) -m pytest --cov=aaa --cov-report=term-missing --cov-fail-under=80

# --- intake targets ---
intake-validate:; $(OFFLINE_RUN) --engagement-id eng-validate-001
                # Offline validation smoke using the UCI German Credit fixture bundle.
intake-demo:    ; $(OFFLINE_RUN) --engagement-id eng-demo-001
                # Full offline demo: IntakeValidator → Orchestrator → final verdict.

# --- exposé milestones ---
m3-linear:    ; $(OFFLINE_RUN) --engagement-id eng-m3-001
m4-full:      ; $(OFFLINE_RUN) --engagement-id eng-m4-001
m5-case1:     ; $(OFFLINE_RUN) --engagement-id eng-m5-case1
m5-case2:     ; $(OFFLINE_RUN) --engagement-id eng-m5-case2
m6-case3:     ; $(OFFLINE_RUN) --engagement-id eng-m6-case3
m6-case4:     ; $(OFFLINE_RUN) --engagement-id eng-m6-case4

# --- demo + deploy ---
report-german:; $(OFFLINE_RUN) --engagement-id eng-uci-german-credit-001 --output-file out/eng-uci-german-credit-001.json
demo:         ; AAA_OFFLINE_MODE=true .venv/bin/streamlit run aaa/ui/app.py
deploy-staging:; tofu -chdir=infra/tofu workspace select staging && tofu -chdir=infra/tofu apply -auto-approve
deploy-prod:  ; tofu -chdir=infra/tofu workspace select prod    && tofu -chdir=infra/tofu apply
