"""The model-metadata vocabularies: task types, formats, frameworks, access and artefact kinds."""
from __future__ import annotations

from typing import Literal, get_args

TaskType = Literal[
    "binary_classification", "multiclass_classification",
    "regression", "forecasting", "llm_generation", "anomaly_detection",
]
ModelFormat = Literal[
    "pickle", "joblib", "onnx", "pytorch", "huggingface", "safetensors",
    "huggingface_pretrained", "huggingface_adapter",
]
ModelFramework = Literal[
    "sklearn", "transformers", "onnxruntime",
    "sklearn_wrapper", "chronos_sklearn_wrapper",
    "huggingface", "huggingface_transformers", "huggingface_peft",
]
ModelAccessMode = Literal[
    "artifact_upload", "registry_reference",
    "base_plus_adapter", "hosted_api", "not_provided",
]
#: Whether an uploaded artefact is one file or a bundle of them (fix F7).
#: Distinct from :func:`aaa.platform.artifact_loader.infer_kind`, which names a
#: *deserialisation* target; this names a **layout**, and S6 needs it because
#: guessing it from the URI string is how a directory model gets loaded as a
#: pickle. See :mod:`aaa.tools.model_meta.artifact_layout`.
ModelArtifactKind = Literal["single_file", "directory"]
ModelProvider = Literal[
    "huggingface", "openai", "azure_openai", "anthropic", "google_gemini",
    "openrouter", "nvidia_nim", "aws_bedrock", "mistral", "cohere",
    "self_hosted", "other",
]
#: Runtime views of the Literal vocabularies (kept in sync via ``get_args``).
TASK_TYPES: tuple[str, ...] = get_args(TaskType)
MODEL_FORMATS: tuple[str, ...] = get_args(ModelFormat)
MODEL_FRAMEWORKS: tuple[str, ...] = get_args(ModelFramework)
ACCESS_MODES: tuple[str, ...] = get_args(ModelAccessMode)
MODEL_PROVIDERS: tuple[str, ...] = get_args(ModelProvider)
ARTIFACT_KINDS: tuple[str, ...] = get_args(ModelArtifactKind)
#: Task types whose datasets carry a label column.
#:
#: ``anomaly_detection`` is deliberately absent. An isolation forest is fitted
#: without labels, and the S6 contract agrees — its ``positive_label`` rule reads
#: *"null for regression/forecasting/LLM/anomaly detection"*. Demanding a
#: ``target_column`` for it would reproduce, one field over, the mis-declaration
#: that widening ``TaskType`` just removed.
SUPERVISED_TASK_TYPES: tuple[str, ...] = (
    "binary_classification", "multiclass_classification", "regression", "forecasting",
)
#: Modes where the runnable model is named rather than uploaded, so a
#: :class:`ModelReference` identifying it is mandatory.
REFERENCE_MODES: tuple[str, ...] = (
    "registry_reference", "base_plus_adapter", "hosted_api",
)
#: Modes that supply no artefact bytes, so ``model_format`` describes nothing.
NO_ARTEFACT_MODES: tuple[str, ...] = ("hosted_api", "not_provided")


__all__ = ["ACCESS_MODES", "ARTIFACT_KINDS", "MODEL_FORMATS", "MODEL_FRAMEWORKS", "MODEL_PROVIDERS", "ModelAccessMode", "ModelArtifactKind", "ModelFormat", "ModelFramework", "ModelProvider", "NO_ARTEFACT_MODES", "REFERENCE_MODES", "SUPERVISED_TASK_TYPES", "TASK_TYPES", "TaskType"]
