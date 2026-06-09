"""
aaa.dagster.jobs — Dagster job definitions.

Jobs
----
full_audit_job
    Runs the complete 6-phase audit pipeline for a single engagement.
    Dependency chain: intake → P1 → P2 → P3 → P4 → P5 → P6 + cost_summary.

cost_monitoring_job
    Standalone job that reads the audit JSONL and surfaces LLM cost metadata.
    Safe to run at any time without triggering an audit.

Schedules / sensors are defined in ``aaa.dagster.sensors``.
"""
from __future__ import annotations

from dagster import define_asset_job, AssetSelection

from aaa.dagster.assets import (
    intake_validation_asset,
    phase1_scope_asset,
    phase2_data_asset,
    phase3_model_asset,
    phase4_fairness_asset,
    phase5_governance_asset,
    phase6_report_asset,
    llm_cost_summary_asset,
)

# Full pipeline — all audit phase assets
full_audit_job = define_asset_job(
    name="full_audit_job",
    selection=AssetSelection.assets(
        intake_validation_asset,
        phase1_scope_asset,
        phase2_data_asset,
        phase3_model_asset,
        phase4_fairness_asset,
        phase5_governance_asset,
        phase6_report_asset,
    ),
    description="End-to-end EU AI Act audit pipeline (Stage 0 → Phase 6).",
)

# Cost / observability job — runs independently
cost_monitoring_job = define_asset_job(
    name="cost_monitoring_job",
    selection=AssetSelection.assets(llm_cost_summary_asset),
    description="Aggregate LLM token/cost metrics from the audit log.",
)

# Phase-level partial jobs (useful for re-running individual phases)
intake_only_job = define_asset_job(
    name="intake_only_job",
    selection=AssetSelection.assets(intake_validation_asset),
    description="Run Stage 0 intake validation only.",
)

phase1_only_job = define_asset_job(
    name="phase1_only_job",
    selection=AssetSelection.assets(intake_validation_asset, phase1_scope_asset),
    description="Run Stage 0 + Phase 1 scope verification.",
)

__all__ = [
    "full_audit_job",
    "cost_monitoring_job",
    "intake_only_job",
    "phase1_only_job",
]
