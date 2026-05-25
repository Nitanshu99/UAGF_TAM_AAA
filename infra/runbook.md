# AAA — Operational Runbook (§14.9)

This document is the on-call playbook for the AAA platform. It mirrors the
incident table in `ARCHITECTURE.md §14.9` and provides the exact commands to
run for each scenario. Keep it in sync with the architecture document; the
table below is authoritative.

## Incident response matrix

| Incident | Detection | First action | Escalation |
|---|---|---|---|
| Engagement stuck > 2 h | Cost dashboard SLA breach | `python -m aaa.cli resume --engagement {id}` (uses LangGraph checkpoint) | HITL review if 3 reruns fail |
| `cgsa_pull` 5xx > 5 min | Langfuse alert on `cgsa_pull_error_rate` | Check S4 status page; flip engagement to HITL pause via `aaa.cli pause --engagement {id}` | Email supervisor; open S5↔S4 ticket |
| Schema drift on nightly contract | GitHub issue auto-opened by `s4_contract.yml` | Inspect diff; if non-breaking, bump `CGSA_SCHEMA_VERSION` + PR; if breaking, freeze new audits | Joint S4↔S5 sync meeting |
| MinIO disk > 80 % | Grafana alert | `restic forget --keep-last 30 --prune` on backup repo; expand volume | On-call rota |
| LLM provider outage | LiteLLM auto-fallback engaged | Verify fallback model in Langfuse; downgrade audit confidence flag | If all fallbacks down, pause new engagements |
| Verifier `escalate_hitl` spike | Langfuse anomaly on `verifier_escalation_rate` | Inspect last 10 critiques; if prompt regression, roll back agent prompt version | Notify prompt owner |
| Client right-to-erasure request | GDPR ticket | `python -m aaa.cli purge --engagement {id}` (drops Postgres schema + MinIO prefix + Langfuse trace) | Log in DPA register |

## Standard procedures

### S1. Bring the stack up (clean host)

```bash
cp .env.example .env                 # fill in real secrets
docker compose pull
docker compose up -d
alembic upgrade head                 # runs the initial migration
curl -sf http://localhost:8000/healthz
```

**macOS only — pre-warm heavy imports before running the ingestion pipeline.**
On the first run after a fresh install, macOS Gatekeeper must verify every native `.so` extension (qdrant_client, sklearn, nltk, numpy). The ingestion script does this automatically at startup, but if you are scripting the pipeline non-interactively you can also trigger it manually to avoid any timeout issues:

```bash
.venv/bin/python -c "import numpy, sklearn, nltk, qdrant_client; print('warm-up OK')"
```

Run this once after installing dependencies; subsequent runs skip Gatekeeper verification.

### S2. Promote staging → prod

```bash
tofu -chdir=infra/tofu workspace select prod
tofu -chdir=infra/tofu apply
ssh root@<prod-host> 'cd /opt/aaa && \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d'
```

### S3. OpenBao seal/unseal

OpenBao starts sealed on production hosts. To unseal:

```bash
ssh root@<host>
docker exec -it openbao bao operator unseal <key-shard-1>
docker exec -it openbao bao operator unseal <key-shard-2>
docker exec -it openbao bao operator unseal <key-shard-3>
docker exec -it openbao bao status
```

Key shards live in three separate offline locations (see §11). Never store
shards together.

### S4. Backup / restore (MinIO + Postgres)

Backups run nightly via `restic` to an off-site S3 bucket:

```bash
# manual backup
restic -r s3:https://<backup-endpoint>/<bucket> backup \
  /var/lib/docker/volumes/postgres_data \
  /var/lib/docker/volumes/minio_data

# restore (point-in-time)
restic -r s3:https://<backup-endpoint>/<bucket> snapshots
restic -r s3:https://<backup-endpoint>/<bucket> restore <snapshot-id> \
  --target /restore
```

### S5. Schema-drift response

1. Review the issue opened by `s4_contract.yml`.
2. Inspect the `schema_drift.json` artefact attached to the run.
3. **Non-breaking (added optional field):** bump `CGSA_SCHEMA_VERSION` in
   `.env` and `aaa/settings.py`; vendor the new schema under
   `schemas/cgsa/v1.0.1/`; open PR.
4. **Breaking (removed/renamed required field):** stop scheduling new
   engagements (`aaa.cli pause --all`); convene S4↔S5 sync; either S4 reverts
   or AAA writes a migration shim in `aaa/tools/cgsa_ingest.py`.

### S6. Right-to-erasure (GDPR Art. 17)

```bash
python -m aaa.cli purge --engagement <id> --confirm
# Verifies cascade delete of:
#   - Postgres rows (engagements, evidence_artefacts, langgraph_checkpoints)
#   - MinIO prefix engagements/<id>/
#   - Langfuse traces tagged engagement=<id>
```

The command exits non-zero if any object remains; log the run-id in the DPA
register.

## Contacts

- **On-call rota:** see `#aaa-oncall` channel.
- **Schema/contract:** S4 maintainers (see UAGF_TAM_S4 repo).
- **Supervisor:** thesis supervisor (DPA agreement signatory).

## See also

- `ARCHITECTURE.md §11` — Security & multi-tenancy
- `ARCHITECTURE.md §14.4` — Local Docker Compose stack
- `ARCHITECTURE.md §14.8` — Production topology
