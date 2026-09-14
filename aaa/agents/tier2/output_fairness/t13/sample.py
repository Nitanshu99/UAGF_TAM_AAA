"""Prediction-sample assembly for the T13 sampling log."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.context import TOXICITY_SAMPLE_CAP, FairnessInputs


def coerce_jsonable(value: Any) -> Any:
    """Coerce arbitrary values to JSON-safe scalars for T13 entries.

    :param value: Any prediction / label / attribute value.
    :returns: A JSON-serialisable scalar, or ``None`` when impossible.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    try:
        return str(value)
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def build_predictions_sample(inp: FairnessInputs) -> list[dict[str, Any]]:
    """Build the capped per-prediction sample entries for T13.

    :param inp: Resolved Phase 4 inputs.
    :returns: Up to :data:`TOXICITY_SAMPLE_CAP` sample entries.
    """
    preds = list(inp.y_pred or [])[:TOXICITY_SAMPLE_CAP]
    trues = list(inp.y_true or [])
    feats = list(inp.sensitive_features or [])
    texts = list(inp.prediction_texts or [])
    ids = list(inp.prediction_ids or range(len(preds)))[:len(preds)]
    if len(ids) < len(preds):
        ids.extend(range(len(ids), len(preds)))
    sample: list[dict[str, Any]] = []
    for i, pred in enumerate(preds):
        entry: dict[str, Any] = {"prediction_id": str(ids[i]),
                                 "predicted_value": coerce_jsonable(pred)}
        if i < len(trues):
            entry["true_value"] = coerce_jsonable(trues[i])
        if i < len(feats) and inp.sensitive_feature_names:
            entry["sensitive_attributes"] = {
                inp.sensitive_feature_names[0]: coerce_jsonable(feats[i])}
        if i < len(texts):
            entry["input_excerpt"] = str(texts[i])[:200]
        sample.append(entry)
    return sample
