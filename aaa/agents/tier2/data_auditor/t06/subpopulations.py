"""What Phase 2 measured about the labels, for the datasheet's impact-on-subpopulations answer.

``uses.impact_on_subpopulations`` was always null, while the same phase had measured
the recorded labels' positive rate by group and found three attributes well below
the highest group's rate (live run bb7837). The
datasheet question asks exactly that (Gebru et al., 2021, "Uses"), so it is answered
from the measurement — or left null when nothing could be measured. The answer
carries each ratio's interval, and says what the interval decides.

The decision is named, not implied: case 06's CLI run had T06 refused because the text
said an interval "spans 0.8" without recording the resulting four-fifths decision per
attribute (T-20260914-064).
"""
from __future__ import annotations

from typing import Any

#: ``four_fifths_passed`` → (the interval's relation to 0.8, the decision it records).
_DECISIONS = {False: ("wholly below 0.8", "adverse"), None: ("which spans 0.8", "undecided"),
              True: ("at or above 0.8", "within")}


def _disparity(attribute: dict[str, Any]) -> str:
    """"region 0.62 (B vs A; interval 0.41–0.93, which spans 0.8; four-fifths decision: undecided)"."""
    relation, decision = _DECISIONS[attribute.get("four_fifths_passed")]
    interval = attribute.get("ratio_interval") or {}
    bounds = (f"interval {interval['low']}–{interval['high']}, {relation}; "
              if "low" in interval and "high" in interval else "")
    return (f"{attribute['attribute']} {attribute['ratio']} "
            f"({attribute['lowest_group']} vs {attribute['highest_group']}; "
            f"{bounds}four-fifths decision: {decision})")


def impact_on_subpopulations(label_bias: dict[str, Any] | None) -> str | None:
    """The measured label disparity as a datasheet answer, or ``None`` when unmeasured.

    :param label_bias: :func:`aaa.tools.label_disparity.label_disparity` output.
    """
    tested = [a for a in (label_bias or {}).get("attributes") or [] if a.get("tested")]
    if not (label_bias or {}).get("computed") or not tested:
        return None
    target = (label_bias or {}).get("target_column")
    adverse = [a for a in tested if a.get("four_fifths_passed") is False]
    undecided = [a for a in tested if a.get("four_fifths_passed") is None]
    within = [a for a in tested if a.get("four_fifths_passed") is True]
    parts = [f"Measured in Phase 2 on the recorded labels ({target}), with 95% intervals "
             "adjusted for the number of group comparisons."]
    if adverse:
        parts.append("Positive-label rates fall below the four-fifths ratio for "
                     f"{'; '.join(_disparity(a) for a in adverse)}; any use that learns from "
                     "or is evaluated against these labels inherits that disparity.")
    if undecided:
        parts.append("The sample cannot place the ratio above or below four-fifths for "
                     f"{'; '.join(_disparity(a) for a in undecided)}.")
    if within:
        parts.append("Rates are within the four-fifths ratio for "
                     f"{'; '.join(_disparity(a) for a in within)}.")
    return " ".join(parts)


__all__ = ["impact_on_subpopulations"]
