"""The confidence a Tier-3 spawn reports, from whether its specialist tool ran.

The privacy, cyber and L-branch spawns reported 0.9 / 0.85 / 0.9 whatever happened:
a privacy deep-dive with no dataset to scan, a cyber audit whose probes were skipped
and an L-branch that scored nothing all closed as confident as a full run. Tier-2
agents already report 0.6 when their evidence is degraded; a spawn now does too.
0.6 is the ``CONFIDENCE_FLOOR`` itself, so the number stays descriptive: whether a
spawn's articles lose their evidence is decided from its recorded procedure outcomes
by :mod:`aaa.platform.audit_programme`, not from a self-reported score.
"""
from __future__ import annotations

#: Reported when the spawn's specialist tool did not run.
DEGRADED_CONFIDENCE = 0.6


def spawn_confidence(when_run: float, tool_ran: bool) -> float:
    """*when_run* if the specialist tool produced a measurement, else the degraded value.

    :param when_run: The spawn's confidence over a completed measurement.
    :param tool_ran: Whether that measurement exists.
    """
    return when_run if tool_ran else DEGRADED_CONFIDENCE


__all__ = ["DEGRADED_CONFIDENCE", "spawn_confidence"]
