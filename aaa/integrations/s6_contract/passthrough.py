"""The S5 stage_b keys that reach S6 unchanged, and the ones its vocabulary checks."""
from __future__ import annotations

from aaa.integrations.s6_contract import vocabulary as vocab

#: S5 stage_b keys that pass through unchanged, in the sheet's own order.
#: ``sensitive_feature_columns`` is excluded — it needs :func:`_sensitive_feature_columns`,
#: not a raw passthrough (finding S19).
_STAGE_B_PASSTHROUGH = (
    "task_type", "model_artifact_uri", "model_artifact_kind", "model_entrypoint",
    "model_format", "model_framework", "model_type", "model_access_mode",
    "model_reference", "training_dataset_uri", "evaluation_dataset_uri",
    "target_column", "positive_label",
    "immutable_feature_columns", "actionable_feature_columns",
    "golden_set_uri", "system_prompt_uri", "rag_manifest_uri", "guardrail_config_uri",
)
#: field name → the S6 vocabulary it must belong to.
_CHECKED = (
    ("modality", vocab.MODALITIES), ("system_type", vocab.SYSTEM_TYPES),
    ("risk_tier", vocab.RISK_TIERS), ("application_domain", vocab.APPLICATION_DOMAINS),
    ("task_type", vocab.TASK_TYPES), ("model_format", vocab.MODEL_FORMATS),
    ("model_framework", vocab.MODEL_FRAMEWORKS),
    ("model_artifact_kind", vocab.ARTIFACT_KINDS),
    ("governance_verdict", vocab.GOVERNANCE_VERDICTS),
)


__all__ = ["_CHECKED", "_STAGE_B_PASSTHROUGH"]
