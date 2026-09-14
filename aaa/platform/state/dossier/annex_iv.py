"""The Annex IV §1–§9 technical-documentation dossier uploaded in Stage B."""
from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from aaa.platform.state.model_meta import ModelReference
from aaa.platform.state.model_vocab import (
    ModelAccessMode,
    ModelArtifactKind,
    ModelFormat,
    ModelFramework,
    TaskType,
)


class AnnexIVDossier(TypedDict):
    """Annex IV §1–§9 technical documentation uploaded in Stage B."""
    general_description: str
    model_type: str
    design_process: str
    training_data_description: str
    data_governance_measures: str
    monitoring_measures: str
    logging_capabilities: str
    accuracy_metrics: dict[str, float]
    robustness_metrics: dict[str, float] | None
    risk_management_file_uri: str | None
    lifecycle_change_log: list[str]
    harmonised_standards: list[str]
    other_standards: list[str]
    eu_doc_uri: str | None
    post_market_plan_uri: str | None
    system_prompt_uri: str | None
    rag_manifest_uri: str | None
    tool_inventory: list[str] | None
    guardrail_config_uri: str | None
    golden_set_uri: str | None
    # JSON array of trace objects ({"id", "steps": [{"type": "tool_call",
    # "tool_name", "depth"}]}) exported from the client's own agentic-system
    # tracing (Langfuse-shaped or equivalent) — consumed by trajectory_audit.
    trace_sample_uri: NotRequired[str | None]
    # ── Independent-analysis inputs (populated by UI upload flow / fixtures) ────
    # URIs to the real artefacts the audit re-runs against, and a minimal data
    # dictionary so agents can split X/y and scope protected-attribute fairness
    # testing. All NotRequired for backward compatibility with legacy fixtures.
    model_artifact_uri: NotRequired[str | None]
    # Layout of what `model_artifact_uri` points at, and what to load inside it
    # (fix F7). Absent from every delivered state until 2026-09-06, so S6 had to
    # infer a bundle from the URI string; `model_entrypoint` is required when
    # `model_artifact_kind` is "directory" — the final path is
    # `model_artifact_uri` / `model_entrypoint`.
    model_artifact_kind: NotRequired[ModelArtifactKind | None]
    model_entrypoint: NotRequired[str | None]
    training_dataset_uri: NotRequired[str | None]
    evaluation_dataset_uri: NotRequired[str | None]
    target_column: NotRequired[str | None]
    positive_label: NotRequired[Any]
    sensitive_feature_columns: NotRequired[list[str] | None]
    # Counterfactual (DiCE) actionability constraints. Without them the
    # generator infers which features may move from their *names*, which is how
    # a counterfactual ends up recommending the applicant change their age.
    immutable_feature_columns: NotRequired[list[str] | None]
    actionable_feature_columns: NotRequired[list[str] | None]
    # S6 hand-off vocabulary (agreed 2026-07): required by S6 to load and
    # evaluate the model artefact; validated in intake when a model is uploaded.
    task_type: NotRequired[TaskType | None]
    model_format: NotRequired[ModelFormat | None]
    model_framework: NotRequired[ModelFramework | None]
    feature_columns: NotRequired[list[str] | None]
    data_dictionary: NotRequired[dict[str, Any] | None]
    # Provenance (2026-08): how S6 obtains a runnable model, and the vendor-side
    # identity when it is named rather than uploaded. Without these a dossier
    # can declare a format backed by no artefact at all — see ModelReference.
    model_access_mode: NotRequired[ModelAccessMode | None]
    model_reference: NotRequired[ModelReference | None]
