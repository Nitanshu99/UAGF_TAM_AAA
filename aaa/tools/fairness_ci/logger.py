"""Confidence-level constants for the fairness intervals."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Two-sided confidence level reported beside every fairness metric.
CONFIDENCE_LEVEL: float = 0.95

#: Normal quantile for :data:`CONFIDENCE_LEVEL`.
Z: float = 1.959963984540054

#: The four-fifths rule: a group selected at under 80 % of another group's rate
#: shows adverse impact (EEOC Uniform Guidelines on Employee Selection
#: Procedures, 29 CFR §1607.4(D)). The one fairness comparator here with a
#: regulatory source, and it is always compared with an interval — the same
#: section warns against reading impact into numbers "too small to be reliable".
FOUR_FIFTHS: float = 0.8

__all__ = ["logger", "CONFIDENCE_LEVEL", "FOUR_FIFTHS", "Z"]
