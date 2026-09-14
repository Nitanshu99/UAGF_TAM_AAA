"""Why Phase 4 could not test output fairness, established rather than guessed.

T12 used to give one sentence for every untested run: "No predictions or
protected-attribute columns available". In case 06 neither was the cause — the
phase had been dispatched as generative and loaded nothing — and the data
dictionary declared five protected attributes the sentence said were missing
(T-20260913-011). The evaluation loader stops at a definite step, and what it
populated before stopping says which one, so the cause is read from that.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.data_dictionary import explicit_data_dictionary
from aaa.tools.eval_inputs.uris import resolve_input_uris

GENERATIVE_ONLY = "generative_only"
NO_EVALUATION_DATASET = "no_evaluation_dataset"
EVALUATION_SET_UNUSABLE = "evaluation_set_unusable"
MODEL_NOT_ACCESSIBLE = "model_not_accessible"
MODEL_NOT_SCORABLE = "model_not_scorable"
NO_PROTECTED_ATTRIBUTES = "no_protected_attributes"


def declared_context(stage_b: dict[str, Any], t01b: dict[str, Any]) -> dict[str, Any]:
    """What the provider declared that a reason should quote.

    :param stage_b: The Annex IV dossier.
    :param t01b: The stored T01b artefact.
    :returns: Declared protected attributes, model access mode and evaluation URI.
    """
    _, eval_uri, _, access_mode = resolve_input_uris(stage_b or {}, t01b or {})
    block = explicit_data_dictionary(stage_b or t01b or {})
    return {"declared_attributes": [str(c) for c in block.get("sensitive_feature_columns") or []],
            "model_access_mode": access_mode, "evaluation_dataset_uri": eval_uri}


def diagnose(scored: Any) -> str | None:
    """The step the evaluation loader stopped at, as a cause.

    :param scored: The loader's :class:`~aaa.tools.eval_inputs.ScoredEvaluation`.
    :returns: A cause constant, or ``None`` when predictions and protected
        attributes are both available.
    """
    if scored.scored:
        return None if scored.sensitive_features else NO_PROTECTED_ATTRIBUTES
    if scored.y_true is None:
        return NO_EVALUATION_DATASET if scored.data_dict is None else EVALUATION_SET_UNUSABLE
    return MODEL_NOT_ACCESSIBLE if scored.model is None else MODEL_NOT_SCORABLE


__all__ = ["EVALUATION_SET_UNUSABLE", "GENERATIVE_ONLY", "MODEL_NOT_ACCESSIBLE",
           "MODEL_NOT_SCORABLE", "NO_EVALUATION_DATASET", "NO_PROTECTED_ATTRIBUTES",
           "declared_context", "diagnose"]
