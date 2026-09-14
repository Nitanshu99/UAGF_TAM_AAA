"""Part 1 of the former ``intake_completeness_calculator`` module (auto-split)."""
from __future__ import annotations

from dataclasses import dataclass

SECTION_WEIGHTS: dict[int, float] = {
    1: 0.20,  # General description
    2: 0.15,  # Design and development
    3: 0.10,  # Monitoring and control
    4: 0.15,  # Performance metrics
    5: 0.15,  # Risk management (Art. 9)
    6: 0.05,  # Lifecycle changes
    7: 0.10,  # Standards applied
    8: 0.05,  # EU declaration of conformity
    9: 0.05,  # Post-market monitoring plan
}


GATE_THRESHOLD = 0.80


_SECTION_FIELDS: dict[int, list[str]] = {
    1: ["general_description", "model_type"],
    2: ["design_process", "training_data_description", "data_governance_measures"],
    3: ["monitoring_measures", "logging_capabilities"],
    4: ["accuracy_metrics"],
    5: ["risk_management_file_uri"],
    6: ["lifecycle_change_log"],
    7: ["harmonised_standards"],
    8: ["eu_doc_uri"],
    9: ["post_market_plan_uri"],
}


_L_BRANCH_CONDITIONAL: dict[str, str] = {
    "system_prompt_uri": "llm/agentic/gpai",
    "rag_manifest_uri": "llm/agentic/gpai",
    "guardrail_config_uri": "llm/agentic/gpai",
    "golden_set_uri": "llm/agentic/gpai",
    "tool_inventory": "agentic",
}


_L_BRANCH_MODALITIES = {"llm", "agentic", "gpai"}


@dataclass
class SectionScore:
    """Per-section completeness score, its weight, and a display label."""

    score: float
    weight: float
    label: str
