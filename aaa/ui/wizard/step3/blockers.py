"""What still blocks the run: required Stage A fields, and the conditional Stage B ones."""
from __future__ import annotations

from aaa.ui.wizard.step3.required_fields import (
    _CONDITIONAL_LABELS,
    _REQUIRED_STAGE_A,
    _conditional_stage_b_blanks,
    _required_stage_a_blanks,
)


def _blockers(score, gate) -> list[str]:
    """Everything standing between this form and a run, in the customer's words.

    M27: the 0.80 gate scores Annex IV *Stage B* sections, so a Stage A field
    the schema requires could be empty and the run still start — the audit then
    died inside IntakeValidator and surfaced a raw ``provider_name: '' should be
    non-empty`` on the results screen, after the customer had committed to the
    run. M29 is the same late failure one layer down, for the fields a
    language-model or agentic modality additionally requires.

    :param score: Live completeness score (may be ``None``).
    :param gate: Scope-gate result with ``halt_engagement``.
    :returns: One sentence per reason the audit cannot start.
    """
    reasons: list[str] = []
    if gate.halt_engagement:
        reasons.append("This system is out of scope for the audit — see the "
                       "scope card above.")
    blanks = _required_stage_a_blanks()
    if blanks:
        reasons.append("Under **Your system**, complete "
                       + ", ".join(f"**{label}**" for label in blanks) + ".")
    conditional = _conditional_stage_b_blanks()
    if conditional:
        reasons.append(
            "Your declared modality needs "
            + ", ".join(f"**{c}**" for c in conditional)
            + " under **Documents, model & data** — the Annex IV dossier is "
              "incomplete without them.")
    if score is not None and score < 0.80:
        reasons.append(f"Completeness is {score:.0%}; the audit starts at 80%. "
                       "The panel above lists what is worth the most.")
    return reasons


__all__ = ["_CONDITIONAL_LABELS", "_REQUIRED_STAGE_A", "_blockers", "_conditional_stage_b_blanks", "_required_stage_a_blanks"]
