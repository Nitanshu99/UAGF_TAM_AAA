"""Logger for the demographic_parity tool.

The tool measures; it does not decide. Its verdict bands (``ratio ≥ 0.80 and difference ≤ 0.10 PASS; ratio ≥ 0.60 and difference ≤ 0.20 observations``) had no
source and were applied to the point estimate. The verdict is now reached from
the interval, in :func:`aaa.tools.fairness_ci.annotate_metrics`.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
