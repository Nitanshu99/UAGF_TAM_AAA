"""The T12 ``skipped_reason`` and ``P4-NOT-TESTED`` text for each skip cause.

Every reason quotes the declared protected attributes, so no reason can claim
columns are missing where the data dictionary names them.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness import skip_cause as cause

_REASONS = {
    cause.GENERATIVE_ONLY: ("No discriminative component was dispatched to Phase 4; generative "
                            "outputs are assessed on the UAGF-TAM-L branch."),
    cause.NO_EVALUATION_DATASET: "No evaluation dataset could be loaded, so there were no outcomes to test.",
    cause.EVALUATION_SET_UNUSABLE: ("The evaluation dataset loaded, but its target column could not be "
                                    "resolved from the data dictionary."),
    cause.MODEL_NOT_SCORABLE: "The model loaded but could not score the evaluation set (see Phase 3).",
    cause.NO_PROTECTED_ATTRIBUTES: ("The model was scored, but no declared protected attribute is "
                                    "present in the evaluation set, so there are no groups whose "
                                    "outcome rates could be compared."),
}
_ACTIONS = {
    cause.MODEL_NOT_ACCESSIBLE: ("Provide a scorable model artefact or inference access, or "
                                 "provider-logged predictions for the evaluation set."),
    cause.NO_PROTECTED_ATTRIBUTES: ("Declare the protected or proxy attributes of the natural persons "
                                    "the system's outputs affect and include them in the evaluation "
                                    "set, or document why its outputs affect no group of persons."),
    cause.GENERATIVE_ONLY: "Declare the system's discriminative components, if it has any.",
}


def skipped_reason(skip: str | None, detail: dict[str, Any]) -> str:
    """The sentence T12 records for *skip*.

    :param skip: A cause from :mod:`~aaa.agents.tier2.output_fairness.skip_cause`,
        or ``None`` when inputs were supplied directly.
    :param detail: :func:`~aaa.agents.tier2.output_fairness.skip_cause.declared_context`.
    :returns: The cause, followed by the declared protected attributes.
    """
    if skip == cause.MODEL_NOT_ACCESSIBLE:
        mode = detail.get("model_access_mode") or "not declared"
        base = (f"Model predictions unavailable: model_access_mode={mode}; no model artefact "
                "could be loaded to score the evaluation set.")
    else:
        base = _REASONS.get(skip or "", "No scored predictions paired with protected attributes "
                                        "were available.")
    attributes = ", ".join(detail.get("declared_attributes") or []) or "none declared"
    return f"{base} Declared protected attributes: {attributes}."


def recommendation(skip: str | None) -> str:
    """What the provider can supply so the suite can run."""
    return _ACTIONS.get(skip or "", "Provide a scorable model and a labelled evaluation set "
                                    "carrying the declared protected attributes.")


__all__ = ["recommendation", "skipped_reason"]
