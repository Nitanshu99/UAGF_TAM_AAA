"""Field specification for the Stage B free-text documentation widgets."""
from __future__ import annotations

#: field → (label, help text, placeholder, height); height None → text_input.
_TEXT_FIELDS: dict[str, tuple[str, str, str, int | None]] = {
    "general_description": (
        "General system description",
        "Annex IV §1 — Overall purpose, the problem it solves, who is responsible, and who uses it. "
        "Minimum 50 characters.",
        "e.g. CreditScoreRef is an XGBoost-based credit-risk classifier deployed by Acme Analytics "
        "for retail banking partners...", 100),
    "model_type": (
        "Model architecture / type",
        "Annex IV §1 — Technical type and version. E.g. 'XGBoost classifier v1.2', 'BERT fine-tune', "
        "'GPT-4 fine-tune on claims data'.",
        "e.g. XGBoost classifier v1.2", None),
    "design_process": (
        "Design and development process",
        "Annex IV §2 — How was the model designed and trained? Include training methodology, "
        "architecture choices, key iterations. Minimum 30 characters.",
        "e.g. Trained on 3 years of anonymised loan application data using 5-fold cross-validation...", 90),
    "training_data_description": (
        "Training data description",
        "Annex IV §2 / Art. 10 — What datasets were used for training and validation? Include source, "
        "size, date range, and how data was collected. Minimum 30 characters.",
        "e.g. 120,000 anonymised retail loan applications from 2020–2023, sourced from internal CRM...", 90),
    "data_governance_measures": (
        "Data governance measures",
        "Annex IV §2 — Processes governing data quality, access control, and handling "
        "(e.g. anonymisation, consent, bias review). Minimum 20 characters.",
        "e.g. All data anonymised at source, GDPR DPA executed with data owner, quarterly bias review...", 90),
    "monitoring_measures": (
        "Monitoring and control measures",
        "Annex IV §3 — How is the system monitored post-deployment? Include drift detection, human "
        "oversight triggers, and incident response. Minimum 20 characters.",
        "e.g. Monthly PSI drift monitoring, human review triggered when PSI > 0.2, incident log "
        "reviewed quarterly...", 90),
    "logging_capabilities": (
        "Logging capabilities",
        "Annex IV §3 / Art. 12 — What logs does the system produce? Include what events are recorded "
        "and the retention period. Minimum 10 characters.",
        "e.g. All predictions logged with input features (anonymised), output score, and timestamp. "
        "Logs retained 5 years.", 70),
}
