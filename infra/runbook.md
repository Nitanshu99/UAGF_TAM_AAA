# AAA — Operational Runbook

This runbook documents the **currently implemented** operational procedures for
the repository. Where the architecture discusses future production components,
this file only describes what exists in the codebase today.

## Incident response matrix

| Incident | Detection | First action | Escalation |
|---|---|---|---|
| API unhealthy | `GET /healthz` fails or non-200 | inspect `logs/app/app.log` and `logs/api/api.log`; restart `uvicorn aaa.api.main:app --reload --port 8000` | if reproducible, capture `logs/errors/*.jsonl` and open issue |
| Audit request failed | `POST /run` returns 4xx/5xx or engagement status stalls | inspect `logs/errors/*.jsonl`, `logs/audit/llm_audit.jsonl`, and `data/inputs/<id>/` | if model/provider-related, switch to offline/demo path and notify maintainer |
| Persisted result missing | `/api/v1/data/...` or `/report` returns 404 after run | inspect `data/index.json`, `data/results/<id>/`, and runtime logs | if reproducible, open bug against `aaa/data/` or `aaa/api/routes/` |
| Error spike | new files appear under `logs/errors/` or Dagster `error_log_sensor` fires | inspect newest JSONL record and correlate with API/agent log timestamps | escalate if repeated across engagements |
| LLM audit anomaly | abnormal cost/token growth in `logs/audit/llm_audit.jsonl` or Dagster cost summary | inspect agent/model distribution and recent prompt changes | escalate to prompt/model owner |
| Schema version mismatch | `/api/v1/schema-version` differs from expected pinned schema | review `CGSA_SCHEMA_VERSION`, `aaa/settings.py`, and vendored schema files | coordinate schema update before new online runs |
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
python3.12 scripts/setup.py --no-docker --no-migrate
source .venv/bin/activate
AAA_OFFLINE_MODE=true python -m pytest tests/unit -q
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
AAA_OFFLINE_MODE=true python -m pytest tests/unit/test_prompt_registry.py tests/unit/test_prompt_snapshots.py -q
AAA_OFFLINE_MODE=true python -m pytest tests/unit/test_api_routes.py tests/unit/test_data_store.py tests/unit/test_data_api_routes.py -q
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

### S7. Dagster monitoring

```bash
dagster dev -m aaa.dagster.definitions
```

Current Dagster monitoring components:

- `full_audit_job`
- `cost_monitoring_job`
- `intake_only_job`
- `phase1_only_job`
- `error_log_sensor`
- `new_engagement_sensor`

## Backup / restore guidance

The implemented repo persists demo/runtime data locally in `data/` and logs in
`logs/`. For local backup, copy both directories together.

```bash
tar -czf aaa-local-backup.tgz data logs
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
