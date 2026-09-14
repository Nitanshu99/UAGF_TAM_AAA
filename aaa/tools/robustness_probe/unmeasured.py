"""Declared robustness figures the random-perturbation probes cannot re-measure.

Case 01 declares ``adversarial_accuracy_l_inf_0_01 = 0.74`` — accuracy under an L-inf
adversarial attack. The probes perturb inputs at random; they run no such attack, so
the figure was left out of T11 without a word and the Verifier escalated it as untested.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.robustness_probe.degradation import _DECLARED, PROBE_KINDS

#: What the probes do, for the threat-model sentence in T11.
THREAT_MODEL = ("The probes measure stability to random input perturbation — Gaussian noise "
                "scaled to each numeric feature's standard deviation, category flips, character "
                "noise on text — on seeded draws. They are not gradient- or query-based "
                "adversarial attacks, and do not test poisoning or confidentiality attacks "
                "(Art. 15(5)).")


def unmeasured_notes(declared: dict[str, Any] | None) -> list[str]:
    """One sentence per declared ``adversarial_accuracy_<kind>_<level>`` no probe measures.

    :param declared: The provider's ``robustness_metrics``.
    """
    notes = []
    for key, value in (declared or {}).items():
        match = _DECLARED.match(str(key))
        if match and match.group(1) not in PROBE_KINDS and isinstance(value, (int, float)):
            level = match.group(2).replace("_", ".", 1)
            notes.append(f"Declared adversarial accuracy under {match.group(1)} at {level} "
                         f"({float(value):.3f}) is not judged: no probe runs a "
                         f"{match.group(1)} attack.")
    return notes


__all__ = ["THREAT_MODEL", "unmeasured_notes"]
