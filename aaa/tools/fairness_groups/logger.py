"""How a protected attribute is turned into cohorts for a fairness metric.

There is no minimum cohort size. ``MIN_GROUP_SIZE = 30`` refused any grouping with a
smaller cohort — a convention for when a proportion's normal approximation holds,
applied as a verdict. The intervals in :mod:`aaa.tools.fairness_ci` do not rely on
that approximation, and they decide instead: a small cohort gives a wide interval,
and a wide interval gives an undecided result rather than a refusal (2026-09-14).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Above this many distinct values, a numeric attribute is treated as continuous
#: and binned rather than being read as one group per value.  Ten is comfortably
#: above any real categorical encoding (credit-history bands, employment
#: brackets) and far below the 45 distinct ages that manufactured Q2.
MAX_DISCRETE_LEVELS: int = 10

#: Bands a continuous attribute is cut into: quintiles, the conventional split
#: that exposes a monotonic trend across the range. Chosen without looking at the
#: outcomes, so the cut cannot be tuned towards a result.
TARGET_BINS: int = 5

__all__ = ["logger", "MAX_DISCRETE_LEVELS", "TARGET_BINS"]
