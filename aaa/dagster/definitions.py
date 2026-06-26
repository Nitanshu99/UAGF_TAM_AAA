"""
aaa.dagster.definitions — Dagster Definitions entry point.

This module is the ``dagster`` code location target.  Run with::

    dagster dev -m aaa.dagster.definitions

Or point ``pyproject.toml`` at this module::

    [tool.dagster]
    module_name = "aaa.dagster.definitions"

Everything — assets, jobs, resources, sensors, schedules — is registered here.
"""
from dagster import (
    Definitions,
    ScheduleDefinition,
    load_assets_from_modules,
)

from aaa.dagster import assets as assets_module
from aaa.dagster.jobs import (
    full_audit_job,
    cost_monitoring_job,
    intake_only_job,
    phase1_only_job,
)
from aaa.dagster.resources import (
    evidence_store_resource,
    aaa_settings_resource,
)
from aaa.dagster.sensors import error_log_sensor, new_engagement_sensor
from aaa.observability.logging_config import configure_logging

configure_logging()

# ── Asset registry ──────────────────────────────────────────────────────────
all_assets = load_assets_from_modules([assets_module])

# ── Schedules ──────────────────────────────────────────────────────────────
cost_monitoring_schedule = ScheduleDefinition(
    name="hourly_cost_monitoring",
    cron_schedule="0 * * * *",  # every hour
    job=cost_monitoring_job,
    description="Aggregate LLM cost metrics every hour.",
)

# ── Definitions ─────────────────────────────────────────────────────────────
defs = Definitions(
    assets=all_assets,
    jobs=[
        full_audit_job,
        cost_monitoring_job,
        intake_only_job,
        phase1_only_job,
    ],
    resources={
        "evidence_store": evidence_store_resource,
        "aaa_settings": aaa_settings_resource,
    },
    sensors=[error_log_sensor, new_engagement_sensor],
    schedules=[cost_monitoring_schedule],
)
