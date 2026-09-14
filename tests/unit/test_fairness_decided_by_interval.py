"""Fairness is decided by the interval over every cohort pair (T-20260914-023).

Case 05 on MiniMax (2026-09-14): a label ratio of 0.748 over cohorts of 71 and 88 —
an interval of about 0.55 to 1.02 — was held a material Art. 10 breach because it
sat below 0.8. The point estimate is not a measurement of the system; the interval is.
"""
from __future__ import annotations

from aaa.tools.fairness_ci import adjusted_z, difference_decision, ratio_ci, ratio_decision

CASE_05_SEX = {"male": (32, 71), "female": (53, 88)}


def _bounds(interval: tuple[float | None, float | None]) -> tuple[float, float]:
    """Both bounds of an interval that must exist."""
    low, high = interval
    assert low is not None and high is not None
    return low, high


def test_the_case_05_ratio_is_undecided_not_adverse() -> None:
    """Its interval holds both four-fifths and parity."""
    found = ratio_decision(CASE_05_SEX) or {}
    low, high = _bounds(found["interval"])
    assert found["decision"] == "undecided"
    assert low < 0.8 < 1.0 < high
    assert (found["group"], found["baseline"]) == ("male", "female")


def test_the_same_rates_on_a_larger_sample_are_decided() -> None:
    """Thirty times the rows narrows the interval below four-fifths."""
    larger = {g: (k * 30, n * 30) for g, (k, n) in CASE_05_SEX.items()}
    found = ratio_decision(larger) or {}
    assert found["decision"] == "adverse" and _bounds(found["interval"])[1] < 0.8


def test_a_tiny_cohort_does_not_veto_an_established_pair() -> None:
    """The 30-row floor existed to stop this; the pairwise rule does it without a number."""
    found = ratio_decision({"a": (100, 400), "b": (240, 400), "tiny": (0, 3)}) or {}
    assert (found["decision"], found["group"], found["baseline"]) == ("adverse", "a", "b")
    assert found["comparisons"] == 3


def test_within_needs_every_pair_placed() -> None:
    """A cohort too small to place leaves the attribute undecided, not passed."""
    balanced = {"a": (500, 1000), "b": (500, 1000)}
    assert (ratio_decision(balanced) or {})["decision"] == "within"
    assert (ratio_decision({**balanced, "tiny": (1, 3)}) or {})["decision"] == "undecided"


def test_more_cohorts_widen_every_interval() -> None:
    """Choosing the extreme pair after looking is paid for in width (Bonferroni)."""
    assert adjusted_z(10) > adjusted_z(3) > adjusted_z(1)
    one = _bounds(ratio_ci((50, 100), (70, 100), adjusted_z(1)))
    ten = _bounds(ratio_ci((50, 100), (70, 100), adjusted_z(10)))
    assert ten[0] < one[0] and ten[1] > one[1]


def test_a_declared_reference_is_the_only_baseline() -> None:
    """The client's privileged group is compared with each other cohort, and only that."""
    found = ratio_decision({"a": (40, 100), "b": (60, 100), "c": (90, 100)}, reference="b") or {}
    assert found["baseline"] == "b" and found["comparisons"] == 2


def test_a_difference_is_established_only_when_its_interval_excludes_zero() -> None:
    """No tolerance is assumed for a difference; only whether one exists."""
    assert (difference_decision({"a": (100, 400), "b": (240, 400)}) or {})["established"]
    assert not (difference_decision({"a": (3, 5), "b": (1, 5)}) or {})["established"]


def test_an_all_selected_pair_is_not_certain() -> None:
    """Six rows once gave the interval [1, 1]."""
    low, high = _bounds(ratio_ci((3, 3), (3, 3)))
    assert high - low > 0.5
