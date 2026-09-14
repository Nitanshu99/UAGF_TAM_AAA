"""The robustness verdict, from what the probes measured and what the provider declared."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.robustness_probe.degradation import declared_levels, intervals, probe_kind


def _assess(probe: dict[str, Any], clean: Sequence[bool],
            claims: dict[tuple[str, float], float]) -> tuple[str, str | None]:
    """``(outcome, sentence)`` for one probe: overstated, degraded or held."""
    band = intervals(clean, probe["_correct"])
    low, high = band["accuracy"]
    kind, level = probe_kind(probe)
    measured = f"{probe['adversarial_accuracy']:.3f} (95% interval {low:.3f}–{high:.3f})"
    claim = claims.get((kind, level))
    if claim is not None and claim > high:
        return "overstated", (f"Declared adversarial accuracy under {kind} at {level} is "
                              f"{claim:.3f}; the probe measured {measured}.")
    held = "" if claim is None else (
        f"Declared adversarial accuracy under {kind} at {level} ({claim:.3f}) "
        f"{'is corroborated' if claim >= low else 'understates the measurement'}: the probe "
        f"measured {measured}. ")
    if band["drop"][0] > 0:
        return "degraded", (f"{held}{kind} at {level} lowers accuracy to {measured}; the drop "
                            f"of {band['drop'][0]:.3f}–{band['drop'][1]:.3f} on the same rows "
                            "is established.")
    return "held", held.strip() or None


def decide(probes: list[dict[str, Any]], clean: Sequence[bool],
           declared: dict[str, Any] | None) -> tuple[str, list[str]]:
    """The verdict and the sentences that justify it.

    FAIL when a declared robustness figure is overstated; PASS_WITH_OBSERVATIONS when a
    probe establishes a drop; PASS when no probe does; NOT_TESTED with no probe.
    """
    if not probes:
        return "NOT_TESTED", []
    claims = declared_levels(declared)
    assessed = [_assess(p, clean, claims) for p in probes]
    notes = [note for _outcome, note in assessed if note]
    outcomes = {outcome for outcome, _note in assessed}
    verdict = ("FAIL" if "overstated" in outcomes else
               "PASS_WITH_OBSERVATIONS" if "degraded" in outcomes else "PASS")
    return verdict, notes


def _empty_result(modality: str, reason: str | None = None) -> dict[str, Any]:
    return {
        "clean_accuracy": None,
        # Nothing was probed: unknown, not a probe over zero samples (F6).
        "evaluation_sample_size": None,
        "probes": [],
        "overall_robustness_verdict": "NOT_TESTED",
        "min_adversarial_accuracy": None,
        "skipped_reason": reason or f"No model or labels supplied for {modality} robustness probe.",
    }


__all__ = ["_empty_result", "decide"]
