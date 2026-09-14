"""Fix 27 (Q2, Q3) — which groupings a fairness metric may actually be computed over.

The part-2 run raised a **material** non-conformity against the client on `age`.
`age` is a continuous integer, and the suite handed every distinct value to the
metric tools as its own protected group: 45 cohorts drawn from 300 rows, mean 6.7
rows each, smallest **n = 1**.  Six cohorts landed on selection rate 0.0 and two
on 1.0 — which is what a six-row cohort does on a coarse grid — so
``demographic_parity.difference`` came out at exactly 1.0, the maximum the metric
can take.  The number is a property of the cohort count, not of the model, and
the artefact's own disparate-impact check passed the same attribute.

The second material finding has the same shape one step down: `foreign_worker` is
290/10, and ``disparate_impact = 0.660`` is computed on the ten-row group with no
interval and no minimum anywhere in the suite.

One rule follows, and it is this module: a numeric attribute with more levels
than a category has is **binned** into quantile bands before any metric sees it.

A second rule — refuse any grouping whose smallest cohort is under thirty — lived
here until 2026-09-14. It turned a sampling question into a fixed number: case 05's
three cohorts of 18–25 rows were refused outright, while a ratio over 71 and 88 rows
whose interval held parity was read as a breach. Whether a cohort is large enough
is now answered by its interval (:mod:`aaa.tools.fairness_ci.decision`); only a
grouping with a single cohort, which has nothing to compare, is declined here.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Sequence

from aaa.tools.fairness_groups.binning import bin_values, is_continuous
from aaa.tools.fairness_groups.labels import _reason
from aaa.tools.fairness_groups.logger import TARGET_BINS, logger


@dataclass
class GroupResolution:
    """How one protected attribute was grouped, and whether it may be tested."""

    attribute: str
    labels: list[str]
    group_count: int
    smallest_group_size: int
    binned: bool
    tested: bool
    reason: str
    bands: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """The record T12 carries so a reader can see the grouping behind a metric."""
        return {"attribute": self.attribute, "group_count": self.group_count,
                "smallest_group_size": self.smallest_group_size, "binned": self.binned,
                "bands": list(self.bands), "tested": self.tested, "reason": self.reason}




def resolve_groups(attribute: str, values: Sequence[Any], *,
                   target_bins: int = TARGET_BINS) -> GroupResolution:
    """Decide the cohorts *attribute* is tested over.

    :param attribute: Protected-attribute column name.
    :param values: Its raw column, one entry per prediction.
    :param target_bins: Bands to cut a continuous attribute into.
    :returns: The resolved grouping and whether the metrics may be computed.
    """
    binned = is_continuous(values)
    labels = bin_values(values, target_bins) if binned else [str(value) for value in values]
    counts = Counter(labels)
    smallest = min(counts.values()) if counts else 0
    tested = len(counts) >= 2

    resolution = GroupResolution(
        attribute=attribute, labels=labels, group_count=len(counts),
        smallest_group_size=smallest, binned=binned, tested=tested,
        reason=_reason(attribute, values, counts, smallest, binned, tested),
        bands=sorted(counts) if binned else [])
    if not tested:
        logger.warning("Fairness: %s not tested — %s", attribute, resolution.reason)
    elif binned:
        logger.info("Fairness: %s binned into %d band(s); smallest n=%d.",
                    attribute, len(counts), smallest)
    return resolution




__all__ = ["GroupResolution", "resolve_groups"]
