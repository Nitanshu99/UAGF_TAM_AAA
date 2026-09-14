"""Deriving the component modalities a composite system declares."""
from __future__ import annotations

from typing import Any

from aaa.ui.wizard.collect.components import discriminative_evidence
from aaa.ui.wizard.collect.metric_names import _GENERATIVE


def derive_component_modalities(
    declared_modality: str, stage_b: dict[str, Any], declared_ranking: bool | None,
) -> list[dict[str, str]] | None:
    """Build the component list for a generative system, or ``None``.

    :param declared_modality: Stage A's scalar modality.
    :param stage_b: The Stage B payload, for the dossier signals.
    :param declared_ranking: The step-2 answer — ``True``/``False`` when the
        customer answered, ``None`` when they were never asked.
    :returns: A ``component_modalities`` list, or ``None`` to leave the
        declaration scalar (which routes exactly as before).
    """
    if declared_modality not in _GENERATIVE:
        return None
    if declared_ranking is False:
        # Answered "no". Taking the customer's word is the point of asking;
        # the dossier signals stay visible in the finding L1 raises.
        return None

    if declared_ranking:
        role = ("Declared by the customer: the system also ranks, scores, matches "
                "or classifies.")
    else:
        reasons = discriminative_evidence(stage_b)
        if not reasons:
            return None
        role = ("Inferred from the dossier — " + "; ".join(reasons)
                + ". Not asserted by the customer; correct it on the review page "
                  "if the system has no ranking or scoring component.")
    return [
        {"id": "primary", "modality": declared_modality,
         "role": "The generative component named by the declared modality."},
        {"id": "ranking", "modality": "nlp", "role": role},
    ]


__all__ = ["derive_component_modalities"]
