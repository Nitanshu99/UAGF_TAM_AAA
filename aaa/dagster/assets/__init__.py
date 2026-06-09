"""aaa.dagster.assets — Per-phase Dagster asset definitions."""
from aaa.dagster.assets.intake import intake_validation_asset
from aaa.dagster.assets.phase1 import phase1_scope_asset
from aaa.dagster.assets.phase2 import phase2_data_asset
from aaa.dagster.assets.phase3 import phase3_model_asset
from aaa.dagster.assets.phase4 import phase4_fairness_asset
from aaa.dagster.assets.phase5 import phase5_governance_asset
from aaa.dagster.assets.phase6 import phase6_report_asset
from aaa.dagster.assets.llm_cost import llm_cost_summary_asset

__all__ = [
    "intake_validation_asset",
    "phase1_scope_asset",
    "phase2_data_asset",
    "phase3_model_asset",
    "phase4_fairness_asset",
    "phase5_governance_asset",
    "phase6_report_asset",
    "llm_cost_summary_asset",
]
