"""Stage B (Annex IV §1–§9) field-extraction queries."""
from __future__ import annotations

#: Field → plain-English search query for the Annex IV dossier fields.
STAGE_B_QUERIES: dict[str, str] = {
    "general_description": (
        "Provide a general description of this AI system: its overall purpose, "
        "the problem it solves, who is responsible for it, and who the end users are."
    ),
    "model_type": (
        "What is the technical architecture or model type? "
        "e.g. XGBoost classifier v1.2, BERT fine-tune, GPT-4 fine-tune, ResNet-50."
    ),
    "design_process": (
        "How was this model designed and developed? Describe the training methodology, "
        "architecture choices, key design decisions, and iterations."
    ),
    "training_data_description": (
        "What training and validation datasets were used? Include source, size, "
        "date range, and how the data was collected or curated."
    ),
    "data_governance_measures": (
        "What data governance, quality controls, access control, or data management "
        "practices are in place? e.g. anonymisation, consent, bias review."
    ),
    "monitoring_measures": (
        "How is the system monitored after deployment? What oversight mechanisms, "
        "drift detection, or human-in-the-loop triggers exist?"
    ),
    "logging_capabilities": (
        "What logging and audit trail capabilities does the system have? "
        "What events are recorded and what is the retention period?"
    ),
    "accuracy_metrics": (
        "What performance metrics are reported for this system? "
        "e.g. accuracy, AUC, F1 score, precision, recall, RMSE."
    ),
    "lifecycle_change_log": (
        "What significant changes or updates have been made to the system since "
        "initial deployment or the last version?"
    ),
    "harmonised_standards": (
        "What ISO, IEC, or EU harmonised standards has this system been developed "
        "in accordance with? e.g. ISO/IEC 42001:2023, ISO/IEC 23894:2023."
    ),
}
