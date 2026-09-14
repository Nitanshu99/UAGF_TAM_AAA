"""Filename/modality inference of model artefact format, framework, and task type.

Provides the wizard's smart defaults for the S6 hand-off fields
(``model_format``, ``model_framework``, ``task_type``); users can always
override the suggestions before submission.
"""
from __future__ import annotations

from pathlib import PurePosixPath

#: filename extension → (model_format, suggested model_framework or None)
_EXTENSION_MAP: dict[str, tuple[str, str | None]] = {
    ".joblib": ("joblib", "sklearn"),
    ".pkl": ("pickle", "sklearn"),
    ".pickle": ("pickle", "sklearn"),
    ".onnx": ("onnx", "onnxruntime"),
    ".pt": ("pytorch", None),
    ".pth": ("pytorch", None),
    ".safetensors": ("safetensors", "transformers"),
    ".zip": ("huggingface", "transformers"),
}

#: Stage A declared modality → default task_type suggestion
_MODALITY_TASK_MAP: dict[str, str] = {
    "tabular": "binary_classification",
    "time_series": "forecasting",
    "cv": "multiclass_classification",
    "nlp": "multiclass_classification",
    "llm": "llm_generation",
    "agentic": "llm_generation",
    "gpai": "llm_generation",
}


def infer_model_format(filename: str | None) -> tuple[str | None, str | None]:
    """Infer ``(model_format, model_framework)`` from a model artefact filename.

    :param filename: Uploaded artefact filename or URI; ``None``/empty allowed.
    :type filename: str | None
    :returns: Inferred ``(model_format, model_framework)``; either element is
        ``None`` when no confident inference exists. Extension-less names
        (Hugging Face snapshot directories / stub bundles) map to
        ``("huggingface", "transformers")``.
    :rtype: tuple[str | None, str | None]
    """
    if not filename:
        return None, None
    suffix = PurePosixPath(filename.rsplit("/", 1)[-1]).suffix.lower()
    if suffix in _EXTENSION_MAP:
        return _EXTENSION_MAP[suffix]
    if not suffix:  # directory-style upload (e.g. HF snapshot / stub bundle)
        return "huggingface", "transformers"
    return None, None


def suggest_task_type(declared_modality: str | None) -> str | None:
    """Suggest a default ``task_type`` for a Stage A declared modality.

    :param declared_modality: The declared modality (``tabular``, ``llm``, …).
    :type declared_modality: str | None
    :returns: A member of ``TASK_TYPES`` or ``None`` when unknown.
    :rtype: str | None
    """
    return _MODALITY_TASK_MAP.get(declared_modality or "")
