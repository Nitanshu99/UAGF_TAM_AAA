"""Score the model matrix in the dataset's label space and flag a model that cannot score."""
from __future__ import annotations

from typing import Any

from aaa.tools.eval_inputs.label_space import label_space_predictor
from aaa.tools.eval_inputs.scoring import _predict
from aaa.tools.eval_inputs.types import FindingSink
from aaa.tools.findings import make_finding


def score_in_label_space(sink: FindingSink, model: Any, x_model: Any, source_phase: str) -> None:
    """Score *x_model* through the label-space predictor and store it on the sink's result.

    The predictor is kept on the result so every later probe (robustness, cyber)
    scores the same labels the metrics were computed on.

    :param sink: The finding sink whose result carries task type, labels and dictionary.
    :param model: The loaded model.
    :param x_model: The feature matrix built for the model.
    :param source_phase: Tag for an emitted finding.
    """
    result = sink.result
    positive = getattr(result.data_dict, "positive_label", None)
    result.predict_fn = label_space_predictor(model, result.task_type, result.y_true,
                                              1 if positive is None else positive)
    result.y_pred, result.y_proba = _predict(model, x_model, result.predict_fn)
    if result.y_pred is not None:
        return
    sink.add(make_finding(
        finding_id="P3-SCORE",
        description="Loaded model could not score the evaluation set (schema mismatch or "
                    "incompatible preprocessing); metrics could not be recomputed.",
        materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
        recommendation="Ship the model with its preprocessing pipeline matching the eval schema.",
    ), load=True)
