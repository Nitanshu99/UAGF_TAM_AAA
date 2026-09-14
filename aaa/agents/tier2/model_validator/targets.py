"""Declared error-rate targets, checked as the upper bounds they are, against the rate's interval.

Case 03 declared ``target_fnr: 0.02`` and ``target_fpr: 0.10`` and Phase 3 said
"no recomputation exists for this metric family", although both follow from the
confusion matrix (T-20260913-069). A target is met or missed, not corroborated
within a tolerance. Whether it is missed was a comparison of the point estimate, and
a miss became material above a fixed 0.10 gap (T-20260914-050): the Wilson interval
of the rate on the rows it rests on decides instead.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.fairness_ci import wilson
from aaa.tools.findings import make_finding, make_positive_finding

#: Declared target key → (computed metrics key, human label, (errors, other) confusion keys).
TARGET_MAP = {
    "target_fnr": ("fnr", "false-negative rate", ("fn", "tp")),
    "target_fpr": ("fpr", "false-positive rate", ("fp", "tn")),
}


def _interval(confusion: dict[str, int] | None, keys: tuple[str, str]) -> tuple[float, float] | None:
    """The rate's 95% Wilson interval from the confusion counts, or ``None`` without them."""
    if not confusion:
        return None
    errors, other = confusion.get(keys[0], 0), confusion.get(keys[1], 0)
    low, high = wilson(errors, errors + other)
    return None if low is None or high is None else (low, high)


def check_targets(declared: dict[str, Any], computed: dict[str, Any],
                  confusion: dict[str, int] | None = None,
                  ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Findings for declared upper-bound targets the measured rate's interval misses or cannot place.

    :param declared: ``accuracy_metrics`` block from the Stage B dossier.
    :param computed: ``metric_suite`` ``metrics``.
    :param confusion: ``metric_suite`` ``confusion`` counts; without them no target is judged.
    :returns: ``(findings, positive_findings)``.
    """
    findings: list[dict[str, Any]] = []
    positives: list[dict[str, Any]] = []
    for key, (comp_key, label, keys) in TARGET_MAP.items():
        target, measured = declared.get(key), computed.get(comp_key)
        band = _interval(confusion, keys)
        if not isinstance(target, (int, float)) or not isinstance(measured, (int, float)) or not band:
            continue
        fid, span = f"P3-TARGET-{comp_key.upper()}", f"{measured:.3f} (95% interval {band[0]:.3f}–{band[1]:.3f})"
        if band[1] <= target:
            positives.append(make_positive_finding(
                finding_id=fid, articles=["Art.15"], source_phase="P3",
                description=f"Measured {label} {span} meets the declared target of at most {target:.3f}."))
            continue
        missed = band[0] > target
        findings.append(make_finding(
            finding_id=fid, articles=["Art.15"], source_phase="P3",
            description=(f"Measured {label} {span} " + (
                f"exceeds the declared target of at most {target:.3f} on the evaluation set."
                if missed else f"does not establish the declared target of at most {target:.3f}: "
                               "the interval spans it.")),
            materiality="material" if missed else "possibly_material",
            recommendation="Bring the error rate within the declared target, or restate the "
                           "target with its evaluation protocol.",
            declared=float(target), observed=float(measured)))
    return findings, positives


__all__ = ["TARGET_MAP", "check_targets"]
