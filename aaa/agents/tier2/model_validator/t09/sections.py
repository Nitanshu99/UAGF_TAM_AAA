"""Section builders for the T09 model card."""
from __future__ import annotations

from typing import Any, Mapping

from aaa.agents.tier2.model_validator.t09.reasons import (
    ARCHITECTURE_FIELDS,
    TRAINING_FIELDS,
    unrecorded_reason,
)
from aaa.agents.tier2.model_validator.t09.shape import output_shape
from aaa.tools.document_evidence import Evidence

#: A required identity field the intake does not declare. It was "0.0.0" and
#: "Unknown", which read as a declared version and a declared name.
NOT_DECLARED = "not declared"


def identity_section(t01a: dict[str, Any], model_type: str, modality: str) -> dict[str, Any]:
    """Build the T09 ``model_identity`` block from the Stage A declaration."""
    return {
        "model_name": str(t01a.get("system_name") or NOT_DECLARED),
        "model_version": str(t01a.get("version") or NOT_DECLARED),
        "model_type": model_type,
        "modality": modality,
        "provider": t01a.get("provider_name") or None,
    }


def architecture_section(t01b: dict[str, Any], model_type: str,
                         found: Mapping[str, Evidence | None] | None = None,
                         facts: Mapping[str, Any] | None = None,
                         model: Any = None) -> dict[str, Any]:
    """Build the T09 ``architecture`` block from the Annex IV dossier and documents.

    Only ``model_framework`` has a contract key; the shape fields were read from
    keys no contract defines (T-20260913-009). Shapes and the parameter count come
    from the loaded model where it carries them (T-20260913-065); a document
    passage stating the output shape wins; the rest stay ``None`` — unknown.

    :param t01b: T01b Annex IV dossier artefact.
    :param model_type: Resolved model type or modality.
    :param found: Grounded answers to the T09 questions.
    :param facts: :func:`~aaa.tools.model_meta.introspect.model_facts` of the loaded model.
    :param model: The loaded model, if any — named in the reason for null fields.
    :returns: Architecture section dictionary.
    """
    facts = facts or {}
    section = {
        "description": t01b.get(
            "design_process",
            f"{model_type} model — architecture inherited from Annex IV §1–§2."),
        "framework": t01b.get("model_framework"),
        "parameter_count": facts.get("parameter_count"),
        "input_shape": facts.get("input_shape"),
        "output_shape": output_shape(found or {}) or facts.get("output_shape"),
    }
    return {**section, "unrecorded_reason": unrecorded_reason(
        section, ARCHITECTURE_FIELDS, t01b, model)}


def training_section(t01b: dict[str, Any], facts: Mapping[str, Any] | None = None,
                     model: Any = None) -> dict[str, Any]:
    """Build the T09 ``training_regime`` block.

    :param t01b: T01b Annex IV dossier artefact.
    :param facts: Facts of the loaded model; its configured hyperparameters.
    :param model: The loaded model, if any — named in the reason for null fields.
    :returns: Training-regime section dictionary.
    """
    section = {
        "training_data_description": t01b.get(
            "training_data_description", "Not provided — see Annex IV §2."),
        "optimiser": None,
        "loss_function": None,
        "epochs": None,
        "batch_size": None,
        "hyperparameters": (facts or {}).get("hyperparameters"),
        "compute_resources": None,
    }
    return {**section, "unrecorded_reason": unrecorded_reason(
        section, TRAINING_FIELDS, t01b, model)}
