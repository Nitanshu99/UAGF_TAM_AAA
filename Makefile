# AAA — Autonomous AI Auditor: Unified Makefile
# Python 3.12 REQUIRED.

PYTHON := .venv/bin/python
PIP    := .venv/bin/pip

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
intake-validate:; $(PYTHON) -m aaa.cli run --engagement-id eng-validate-001 --intake-dir scripts/fixtures/uci_german_credit --offline
                # Runs IntakeValidator (Stage 0 A/B/C) on the UCI German Credit fixture; prints JSON summary
intake-demo:    ; AAA_OFFLINE_MODE=true CGSA_FIXTURE_DIR=scripts/fixtures/cgsa $(PYTHON) -m aaa.cli run --engagement-id eng-demo-001 --intake-dir scripts/fixtures/uci_german_credit --cgsa-fixture-dir scripts/fixtures/cgsa --offline
                # Full offline demo: IntakeValidator → Orchestrator → final verdict (no LLM calls)

# --- exposé milestones ---
m3-linear:    ; $(PYTHON) -m aaa.cli run --case german_credit --pipeline linear
m4-full:      ; $(PYTHON) -m aaa.cli run --case german_credit --pipeline full
m5-case1:     ; $(PYTHON) -m aaa.cli run --case german_credit --emit-pdf
m5-case2:     ; $(PYTHON) -m aaa.cli run --case m5_forecasting --emit-pdf
m6-case3:     ; $(PYTHON) -m aaa.cli run --case hamburg_hub --emit-pdf
m6-case4:     ; $(PYTHON) -m aaa.cli run --case llm_open --emit-pdf --branch l

# --- demo + deploy ---
report-german:; $(PYTHON) -m aaa.cli run --case german_credit --emit-pdf --open
demo:         ; AAA_OFFLINE_MODE=true .venv/bin/streamlit run aaa/ui/app.py
deploy-staging:; tofu -chdir=infra/tofu workspace select staging && tofu -chdir=infra/tofu apply -auto-approve
deploy-prod:  ; tofu -chdir=infra/tofu workspace select prod    && tofu -chdir=infra/tofu apply
