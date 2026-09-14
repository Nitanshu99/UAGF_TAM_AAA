"""Toxicity probe routing for text modalities (step 6b)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.context import TOXICITY_SAMPLE_CAP, FairnessInputs
from aaa.tools.toxicity_classifier import toxicity_classifier

_TEXT_MODALITIES = {"nlp", "llm", "agentic", "gpai"}


#: Tasks whose outputs are decisions or numbers, never language to screen.
_NON_TEXT_TASKS = {"classification", "regression", "anomaly"}


def outputs_are_text(inp: FairnessInputs, modality: str) -> bool:
    """Whether the system's predictions are language a toxicity screen can read.

    Case 05's CV screener is an ``nlp`` system whose predictions are the labels
    "0"/"1"; screening them found nothing and T13 then claimed its outputs were
    inspected for discriminatory patterns (T-20260913-107).

    :param inp: Resolved Phase 4 inputs.
    :param modality: Normalised system modality.
    """
    if inp.prediction_texts is not None:
        return True
    if (modality or "tabular").lower() not in _TEXT_MODALITIES or inp.task_type in _NON_TEXT_TASKS:
        return False
    labels = {str(v) for v in (inp.y_true if inp.y_true is not None else [])}
    predicted = {str(v) for v in (inp.y_pred if inp.y_pred is not None else [])}
    return bool(predicted) and not (labels and predicted <= labels)


def run_toxicity(inp: FairnessInputs, modality: str) -> dict[str, Any]:
    """Scan a capped prediction sample for toxic / discriminatory language.

    Only text is scanned: supplied prediction texts, or the predictions of a text
    system that generates language (:func:`outputs_are_text`). Anything else is
    NOT_TESTED — a credit score or a shortlist label has no language to screen.

    :param inp: Resolved Phase 4 inputs.
    :param modality: Normalised system modality.
    :returns: ``toxicity_classifier`` result dictionary.
    """
    if not outputs_are_text(inp, modality):
        return toxicity_classifier(predictions=None)
    tox_input = inp.prediction_texts if inp.prediction_texts is not None else inp.y_pred
    return toxicity_classifier(predictions=tox_input,
                               prediction_ids=inp.prediction_ids,
                               sample_size=TOXICITY_SAMPLE_CAP)
