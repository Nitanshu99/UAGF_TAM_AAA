"""
aaa.dagster.sensors — Dagster sensors for automated pipeline triggering.

Sensors
-------
error_log_sensor
    Polls ``logs/errors/`` for new JSONL records and fires an alert run
    whenever an error is detected.  In production, connect to PagerDuty /
    Slack via a ``dagster-slack`` or webhook resource.

new_engagement_sensor
    Polls the FastAPI ``/api/v1/engagements`` endpoint (or the in-memory
    store when offline) for engagements whose status is ``intake_submitted``
    and triggers a ``full_audit_job`` run for each.
"""
import json
import os
from pathlib import Path

from dagster import (
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    sensor,
    DefaultSensorStatus,
)

_ERROR_LOG_DIR = Path("logs/errors")
_SEEN_ERRORS_FILE = Path("logs/.seen_errors")


def _seen_errors() -> set[str]:
    if _SEEN_ERRORS_FILE.exists():
        return set(_SEEN_ERRORS_FILE.read_text().splitlines())
    return set()


def _mark_seen(error_ids: list[str]) -> None:
    existing = _seen_errors()
    existing.update(error_ids)
    _SEEN_ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SEEN_ERRORS_FILE.write_text("\n".join(existing))


@sensor(
    name="error_log_sensor",
    description="Triggers an alert run when new errors appear in logs/errors/.",
    minimum_interval_seconds=60,
    default_status=DefaultSensorStatus.RUNNING,
)
def error_log_sensor(context: SensorEvaluationContext):
    """Scan error JSONL files for unseen error IDs."""
    if not _ERROR_LOG_DIR.exists():
        return

    seen = _seen_errors()
    new_ids: list[str] = []
    run_requests = []

    for jsonl_path in _ERROR_LOG_DIR.glob("*.jsonl"):
        with jsonl_path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    record = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                eid = record.get("error_id", "")
                if eid and eid not in seen:
                    new_ids.append(eid)
                    context.log.warning(
                        "New error detected: %s in %s", eid, jsonl_path.name
                    )
                    run_requests.append(
                        RunRequest(
                            run_key=eid,
                            tags={"component": record.get("component", "unknown")},
                        )
                    )

    if new_ids:
        _mark_seen(new_ids)

    return run_requests


@sensor(
    name="new_engagement_sensor",
    description="Triggers full_audit_job for engagements in intake_submitted state.",
    minimum_interval_seconds=30,
    default_status=DefaultSensorStatus.STOPPED,  # enable in production
)
def new_engagement_sensor(context: SensorEvaluationContext):
    """Poll the in-memory store (or API) for pending engagements."""
    try:
        from aaa.api.store import ENGAGEMENTS, INTAKE_PAYLOADS

        run_requests = []
        for eid, record in ENGAGEMENTS.items():
            if record.get("status") == "intake_submitted" and eid in INTAKE_PAYLOADS:
                run_key = f"audit_{eid}"
                run_requests.append(RunRequest(run_key=run_key, run_config={
                    "ops": {"intake_validation": {"config": {"engagement_id": eid}}}
                }))
        return run_requests
    except Exception as exc:
        context.log.error("new_engagement_sensor failed: %s", exc)
        return []


__all__ = ["error_log_sensor", "new_engagement_sensor"]
