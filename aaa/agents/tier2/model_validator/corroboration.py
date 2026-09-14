"""Whether a declared metric is corroborated by the measured one and its uncertainty."""
from __future__ import annotations

from typing import Literal

from aaa.platform.state.findings import Materiality


def judged(label: str, declared: float, measured: float,
           interval: tuple[float, float] | None) -> tuple[Materiality | None | Literal[""], str]:
    """Judge one declared metric against the measured metric's interval.

    :param label: Human name of the metric.
    :param declared: The provider's figure.
    :param measured: The audit's figure.
    :param interval: Its 95% bootstrap interval, or ``None`` when none was computed.
    :returns: ``(materiality, sentence)``: ``None`` when corroborated, ``""`` when not
        judged for want of an interval.
    """
    if interval is None:
        return "", (f"Declared {label} {declared:.3f} beside the measured {measured:.3f}; no "
                    "interval could be computed, so the difference is not judged.")
    low, high = interval
    span = f"the measured {label} {measured:.3f} (95% bootstrap interval {low:.3f}–{high:.3f})"
    if low <= declared <= high:
        return None, f"Declared {label} {declared:.3f} is corroborated: it lies within {span}."
    if declared > high:
        return "material", (f"Declared {label} {declared:.3f} overstates {span} on the "
                            "evaluation set: the declared performance is not supported.")
    return "possibly_material", (f"Declared {label} {declared:.3f} is below {span}: the "
                                 "declaration understates the measured performance.")


__all__ = ["judged"]
