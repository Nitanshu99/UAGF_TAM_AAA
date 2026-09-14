"""Deciding a fairness question from its interval, never from the point estimate.

Fix 27 refused any cohort under thirty rows, and fix 30's interval "reports; it
does not gate". Between them a fixed number decided what could be tested and the
point estimate decided the verdict. Case 05 (MiniMax run, 2026-09-14) held a
material Art. 10 non-conformity on a label-rate ratio of 0.748 over cohorts of 71
and 88 — an interval of about 0.55 to 1.02, which holds parity — and refused its
output fairness outright because one of three cohorts held 18 rows.

The interval is the test. A ratio is *adverse* when its whole interval lies below
the four-fifths comparator, *within* when every pair's interval lies at or above
it, and otherwise *undecided*: the sample can establish neither. A difference is
*established* when an interval excludes zero. No cohort size enters the rule; a
small cohort simply yields a wide interval, and cannot veto a pair that decides.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.fairness_ci.intervals import difference_ci, ratio_ci
from aaa.tools.fairness_ci.logger import FOUR_FIFTHS
from aaa.tools.fairness_ci.pairs import Counts, adjusted_z, ordered_pairs, rate


def ratio_decision(counts: Counts, reference: str | None = None) -> dict[str, Any] | None:
    """The four-fifths question across cohorts.

    :param counts: Selections and rows per cohort.
    :param reference: A declared privileged cohort to compare every other one with.
    :returns: ``None`` when no pair has a selection to compare; otherwise the
        deciding pair — ``decision`` (``adverse``/``within``/``undecided``),
        ``group``, ``baseline``, ``ratio``, ``interval``, ``comparisons``.
    """
    pairs = [(g, b) for g, b in ordered_pairs(counts, reference) if counts[b][0] > 0]
    if not pairs:
        return None
    z = adjusted_z(len(pairs))
    rows = [{"group": g, "baseline": b, "ratio": rate(counts, g) / rate(counts, b),
             "interval": ratio_ci(counts[g], counts[b], z)} for g, b in pairs]
    within = all(r["interval"][0] >= FOUR_FIFTHS for r in rows)
    decision = ("adverse" if any(r["interval"][1] < FOUR_FIFTHS for r in rows)
                else "within" if within else "undecided")
    # The pair reported is the one the decision rests on: the lowest upper bound —
    # the strongest evidence of adverse impact — unless every pair is within, when
    # the lowest lower bound is the one that came closest to failing.
    bound = 0 if decision == "within" else 1
    chosen = min(rows, key=lambda r: (r["interval"][bound], r["group"], r["baseline"]))
    return {**chosen, "decision": decision, "comparisons": len(pairs)}


def difference_decision(counts: Counts) -> dict[str, Any] | None:
    """Whether any two cohorts' rates differ by more than sampling noise.

    :param counts: Successes and trials per cohort (cohorts without trials skipped).
    :returns: ``None`` with fewer than two such cohorts; otherwise ``established``,
        ``group`` (higher rate), ``baseline`` (lower), ``difference``, ``interval``,
        ``comparisons`` — the pair with the largest lower bound when established,
        the widest gap when not.
    """
    pairs = ordered_pairs(counts)
    if not pairs:
        return None
    z = adjusted_z(len(pairs))
    rows = [{"group": high, "baseline": low,
             "difference": rate(counts, high) - rate(counts, low),
             "interval": difference_ci(counts[high], counts[low], z)} for low, high in pairs]
    established = [r for r in rows if r["interval"][0] > 0]
    chosen = (max(established, key=lambda r: (r["interval"][0], r["group"])) if established
              else max(rows, key=lambda r: (r["difference"], r["group"])))
    return {**chosen, "established": bool(established), "comparisons": len(pairs)}


__all__ = ["difference_decision", "ratio_decision"]
