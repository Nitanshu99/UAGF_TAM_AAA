"""Why a T09 model-card field is empty, stated in the card itself.

Case 06 (MiniMax run, 2026-09-14): the card carried ``primary_metric: "not measured"``
— a placeholder in a field that names a metric — and left the architecture and
training fields null with no word on why, while its only limitation asked for "a live
evaluation set" that had in fact been supplied. The reason lived in a Phase 3 finding
the Verifier does not read with the card, and it escalated the card as defective.
"""
from __future__ import annotations

from typing import Any, Mapping

#: Architecture and training fields that are null unless a document or the model states them.
ARCHITECTURE_FIELDS = ("framework", "parameter_count", "input_shape", "output_shape")
TRAINING_FIELDS = ("optimiser", "loss_function", "epochs", "batch_size", "hyperparameters",
                   "compute_resources")


def access_mode(t01b: Mapping[str, Any]) -> str:
    """The declared ``model_access_mode``, or that none was declared."""
    return str(t01b.get("model_access_mode") or "not declared")


def not_measured_reason(metrics_result: Mapping[str, Any], t01b: Mapping[str, Any],
                        model: Any) -> str | None:
    """Why no performance metric was measured, or ``None`` when one was.

    :param metrics_result: ``metric_suite`` output.
    :param t01b: The Annex IV dossier (model access mode, evaluation set).
    :param model: The model Phase 3 loaded, if any.
    """
    if metrics_result.get("primary_metric_value") is not None:
        return None
    dataset = t01b.get("evaluation_dataset_uri")
    supplied = f"the evaluation set ({dataset})" if dataset else "no evaluation set"
    if model is None:
        return (f"no model was supplied (model_access_mode '{access_mode(t01b)}') and no "
                f"scored predictions were available, so {supplied} could not be scored"
                if dataset else f"neither a model nor an evaluation set was supplied "
                f"(model_access_mode '{access_mode(t01b)}')")
    return (f"the model was loaded but {supplied} yielded no metric this model's labels define"
            if dataset else "the model was loaded but no evaluation set was supplied")


def unrecorded_reason(section: Mapping[str, Any], fields: tuple[str, ...],
                      t01b: Mapping[str, Any], model: Any) -> str | None:
    """Why the section's null fields are null, or ``None`` when none is.

    :param section: The built architecture or training section.
    :param fields: The fields that can be null for want of a source.
    :param t01b: The Annex IV dossier.
    :param model: The model Phase 3 loaded, if any.
    """
    empty = [f for f in fields if section.get(f) is None]
    if not empty:
        return None
    source = (f"no model was supplied to read them from (model_access_mode '{access_mode(t01b)}')"
              if model is None else "the loaded model does not expose them")
    return (f"{', '.join(empty)}: not stated in the Annex IV dossier or the supplied "
            f"documents, and {source}; left null rather than estimated.")


__all__ = ["ARCHITECTURE_FIELDS", "TRAINING_FIELDS", "access_mode", "not_measured_reason",
           "unrecorded_reason"]
