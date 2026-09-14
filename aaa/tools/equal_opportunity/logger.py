"""Logger for the equal_opportunity tool.

The tool measures; it does not decide. Its verdict bands (``difference ≤ 0.10 PASS; ≤ 0.20 observations``) had no
source and were applied to the point estimate. The verdict is now reached from
the interval, in :func:`aaa.tools.fairness_ci.annotate_metrics`.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
