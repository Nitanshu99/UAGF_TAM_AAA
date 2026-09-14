"""The audit programme: which procedure supplies which evidence, and whether it can stand alone.

A procedure is *sufficient* when, performed, it can on its own supply the evidence an
article's element needs, and *supplementary* when it only deepens evidence a
sufficient procedure supplies. The distinction is the one assurance standards draw
(ISAE 3000, ISA 500): a procedure that could not be performed is a scope limitation,
and it removes the article's evidence only when nothing else sufficient was performed.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Procedure:
    """One procedure in the programme and the evidence it supplies."""

    title: str
    phase: str
    article: str
    element: str
    sufficient: bool


PROGRAMME: dict[str, Procedure] = {
    "metric_suite": Procedure("Accuracy metrics recomputed on the evaluation set",
                              "P3", "Art.15", "accuracy", True),
    "ranking_metrics": Procedure("Declared ranking metrics recomputed from supplied ranked outputs",
                                 "P3", "Art.15", "accuracy", True),
    "golden_set_evaluation": Procedure("Golden-set evaluation of the system's answers",
                                       "L", "Art.15", "accuracy", True),
    "robustness_probe": Procedure("Robustness probe against the model",
                                  "P3", "Art.15", "robustness", True),
    "prompt_injection_suite": Procedure("Prompt-injection suite against the deployed prompt",
                                        "L", "Art.15", "cybersecurity", True),
    "specialist_adversarial_probe": Procedure("Specialist adversarial probe (Tier-3 cyber)",
                                              "Cyber", "Art.15", "cybersecurity", False),
    "pii_deep_dive": Procedure("Special-category data re-scan (Tier-3 privacy)",
                               "Privacy", "Art.10", "special_category_data", False),
}

PERFORMED = "performed"
NOT_PERFORMED = "not_performed"


def outcome(procedure_id: str, ran: bool, reason: str | None = None) -> dict[str, dict]:
    """A ``procedure_outcomes`` delta entry for *procedure_id*.

    :param procedure_id: A :data:`PROGRAMME` key.
    :param ran: Whether the procedure produced its measurement.
    :param reason: Why it did not, when it did not.
    """
    if procedure_id not in PROGRAMME:
        raise KeyError(f"{procedure_id} is not in the audit programme")
    return {procedure_id: {"outcome": PERFORMED if ran else NOT_PERFORMED,
                           "reason": None if ran else (reason or "not recorded")}}


__all__ = ["NOT_PERFORMED", "PERFORMED", "PROGRAMME", "Procedure", "outcome"]
