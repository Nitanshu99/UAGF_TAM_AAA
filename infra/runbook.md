# AAA — Operational Runbook

This runbook documents the **currently implemented** operational procedures for
the repository. Where the architecture discusses future production components,
this file only describes what exists in the codebase today.

## Incident response matrix

| Incident | Detection | First action | Escalation |
|---|---|---|---|
| API unhealthy | `GET /healthz` fails or non-200 | inspect `logs/app/app.log` and `logs/api/api.log`; restart `uvicorn aaa.api.main:app --reload --port 8000` | if reproducible, capture `logs/errors/*.jsonl` and open issue |
| Audit request failed | `POST /run` returns 4xx/5xx or engagement status stalls | inspect `logs/errors/*.jsonl`, `logs/audit/llm_audit.jsonl`, and `data/inputs/<id>/` | if model/provider-related, switch `PROVIDER` (openai/nvidia) or clear the LLM keys to fall back to rule-based analysis, and notify maintainer |
| Persisted result missing | `/api/v1/data/...` or `/report` returns 404 after run | inspect `data/index.json`, `data/results/<id>/`, and runtime logs | if reproducible, open bug against `aaa/data/` or `aaa/api/routes/` |
| Error spike | new files appear under `logs/errors/`, or `aaa_errors_total` rises in Grafana | inspect newest JSONL record and correlate with API/agent log timestamps | escalate if repeated across engagements |
| LLM audit anomaly | abnormal cost/token growth in `logs/audit/llm_audit.jsonl`, or the cost / token panels on **aaa-overview** | inspect agent/model distribution and recent prompt changes | escalate to prompt/model owner |
| Schema version mismatch | `/api/v1/schema-version` differs from expected pinned schema | review `CGSA_SCHEMA_VERSION`, `aaa/settings/`, and vendored schema files | coordinate schema update before new online runs |
| Rendered PDF unavailable | `/report` returns summary but `/report.pdf` returns 404 | use JSON report as source of truth and inspect report rendering logs | escalate only if PDF is required for deliverable |

> **Not incidents — expected audit outcomes.** A `FAIL` / `adverse` verdict, an
> `INSUFFICIENT_EVIDENCE` article, or a `disclaimer_of_opinion` are legitimate results of an
> evidence-grounded audit, not system errors. `INSUFFICIENT_EVIDENCE` usually means a real
> artefact was missing or unusable (no runnable model, unreadable dataset, or — for the
> governance articles Art.9/12/17/72 — an unreachable CGSA self-assessment; check
> `CGSA_FIXTURE_DIR`). Only treat `/run` as an incident when it returns 4xx/5xx or stalls.

## Standard procedures

### S1. Bring up the offline/dev path

```bash
python3.12 -m scripts.setup --no-docker --no-migrate
source .venv/bin/activate
python -m pytest tests/unit -q
```

### S2. Start the API and verify it

```bash
uvicorn aaa.api.main:app --reload --port 8000
curl -sf http://localhost:8000/healthz
curl -sf http://localhost:8000/api/v1/schema-version
curl -sf http://localhost:8000/metrics > /dev/null
```

### S3. Start the optional local service stack

Use this only when you want online retrieval or to exercise the broader local
infrastructure.

```bash
docker compose up -d
python -m alembic upgrade head
docker compose ps
```

### S4. Run the current smoke tests

```bash
python -m pytest tests/unit/test_prompt_registry.py -q
python -m pytest tests/unit/test_api_customer_workflow.py tests/unit/test_data_api_routes_empty.py -q

# or the gate CI enforces, over the whole suite:
python -m pytest --cov=aaa --cov-fail-under=70 -m "not e2e and not golden and not contract" -q
```

### S5. Inspect persisted engagement data

Default file layout:

```text
data/
  index.json
  inputs/<engagement_id>/
  results/<engagement_id>/
```

Useful checks:

```bash
python - <<'PY'
import json, pathlib
path = pathlib.Path('data/index.json')
print(json.loads(path.read_text()) if path.exists() else {'engagements': []})
PY
```

Or via API:

```bash
curl -sf http://localhost:8000/api/v1/data/engagements
curl -sf http://localhost:8000/api/v1/data/results
```

### S6. Inspect logs and LLM audit trail

```bash
tail -n 50 logs/app/app.log
tail -n 50 logs/api/api.log
tail -n 20 logs/audit/llm_audit.jsonl
ls logs/errors
```

### S7. Metrics and log monitoring

Dagster was removed in the 2026-07 modularization; monitoring is now Prometheus
metrics plus Loki log search, started on demand:

```bash
make obs        # prometheus + loki + alloy + grafana
```

Grafana: `http://localhost:3002` — the provisioned **aaa-overview** dashboard.
Prometheus scrapes the API's `/metrics` on port 8000, so start the API
(`python -m aaa`) or its target shows `health=down` (the dashboard's first
tile says so, and the `AAAApiScrapeDown` rule fires after two minutes).
That one endpoint carries every process's counters: `import aaa` puts
`prometheus_client` into multiprocess mode over `logs/metrics`, so runs from
the Streamlit wizard, `aaa.cli` and `scripts.run_mock_case` are counted too.

Zero-cost end-to-end check of metrics + logs + Langfuse:

```bash
python -m scripts.obs_probe
```

Metrics the dashboard reads, all emitted by `aaa/observability/metrics/`:

| Metric | Emitted from | Panel |
|---|---|---|
| `aaa_llm_calls_total` | `agents/base/audit.py` | calls by agent + status |
| `aaa_llm_latency_seconds` | `agents/base/audit.py` | p50 / p95 per agent |
| `aaa_llm_tokens_total`, `aaa_llm_cost_usd_total` | `agents/base/audit.py` | token rate, cumulative cost |
| `aaa_phase_latency_seconds` | `phases/verification/finish_phase.py` | p95 per phase |
| `aaa_engagements_total` | `api/routes/workflow/{run,finish}.py` | engagements by verdict |
| `aaa_errors_total` | `observability/error_handler/capture_error.py` | errors by component |

| `aaa_phases_total` | `phases/verification/finish_phase.py` | phase outcomes by verdict |

These are labelled counters, so a panel stays empty until the first audit
increments it — an empty dashboard on a fresh stack is expected, not a fault.

Alert rules live in `infra/observability/rules/aaa-alerts.yml` and show on
`http://127.0.0.1:9090/alerts` (no Alertmanager in the local profile).

Logs reach Loki via Alloy, which tails `logs/**/*.{log,jsonl}` under
`job="aaa"`, stamps each line with the record's own timestamp and adds a
`level` label (plus `agent` / `status` on LLM-call rows). Rows from
`llm_audit.jsonl` are shipped as metadata only — the full prompt and reply
stay in the file and in Langfuse. Query in Grafana with `{job="aaa"}`, filter
e.g. `{job="aaa", level="error"}` or `{job="aaa"} | json | engagement_id="eng-…"`.
Alloy's own pipeline view is at `http://127.0.0.1:12345`.

### S7b. Rotate a MinIO service-account secret

The app and Langfuse each use a per-bucket account, never the root key.
Change `MINIO_SECRET_KEY` (app, policy `evidence-rw`) or
`LANGFUSE_S3_SECRET_KEY` (Langfuse, policy `langfuse-rw`) in `.env`, then:

```bash
docker compose up -d --force-recreate minio-init   # re-applies users + policies
docker compose up -d langfuse langfuse-worker      # picks up the new S3 secret
```

`infra/minio/init.sh` is idempotent; it verifies the policy is attached and
fails loudly if not.

### S7c. Loki index schema

`infra/observability/loki-config.yml` switches from boltdb-shipper/v11 to
tsdb/v13 at 2026-09-12 00:00 UTC. The tsdb period was exercised on
2026-09-11 in a throwaway instance (push 204, query served). If Loki logs
errors after the boundary, revert the second `schema_config` entry and
restart Loki; data written before the boundary is unaffected either way.

### S7a. Production overlay: OpenBao init / unseal

`docker-compose.prod.yml` runs OpenBao as a real server with file storage
(`infra/openbao/config.hcl`) instead of `-dev`. Once, after the first start:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec openbao bao operator init
# store the unseal keys and root token outside the host, then (each restart):
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec openbao bao operator unseal
```

A sealed vault reports `unhealthy` in `docker compose ps` on purpose.

### S8. Resolve a provisional (deferred-HITL) report

A run that escalated artefacts produces a **provisional** report
(`report_status = PROVISIONAL_PENDING_HITL`) plus `data/customer/<company>/<id>_hitl_review.json`.
To finalize:

```bash
# 1. fetch the packet (or open the file on disk)
curl -s localhost:8000/api/v1/engagements/<id>/hitl-review | python -m json.tool
# 2. edit each case's human_decision (accept | uphold_escalation | override) + rationale
# 3. apply decisions, recompute, re-render FINAL T17/T18
python -m scripts.finalize_hitl <id>
# 4. confirm the full audit-state
curl -s localhost:8000/api/v1/engagements/<id>/audit-state | python -m json.tool
```

## Backup / restore guidance

The implemented repo persists demo/runtime data locally in `data/` and logs in
`logs/`. For local backup, copy both directories together, plus the two
stores the pipeline writes through Docker: the Postgres cluster (LangGraph
checkpoints and the Langfuse database) and the MinIO evidence bucket.

```bash
tar -czf aaa-local-backup.tgz data logs
docker compose exec -T postgres pg_dumpall -U "$POSTGRES_USER" | gzip > aaa-postgres.sql.gz
docker compose run --rm --entrypoint sh minio-init -c \
  'mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" && mc mirror local/aaa-evidence /backup' \
  # add `-v $PWD/backup:/backup` to keep the mirror on the host
```

Restore by unpacking into the repo root on a compatible checkout.

## Right-to-erasure / engagement deletion

There is **no built-in purge CLI command in the current repository**.

Current manual procedure:

1. remove the engagement's directories under `data/inputs/<id>/` and `data/results/<id>/`
2. remove the corresponding row from `data/index.json`
3. review `logs/` for engagement-specific references if policy requires cleanup
4. record the maintenance action externally

Because this is manual today, treat deletion as a controlled maintenance task.

## Contacts

- **Schema/contract questions:** S4 maintainers
- **Repository/runtime issues:** AAA maintainers
- **Supervisor approvals:** thesis supervisor / project owner

## See also

- `README.md`
- `SETUP.md`
- `ARCHITECTURE.md §14`
