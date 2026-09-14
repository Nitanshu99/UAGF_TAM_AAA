"""T-20260914-003: the results page is dated by the audit's completion, not by viewing."""
from __future__ import annotations

from aaa.ui.wizard.step4.verdict import completed_on


def test_the_chip_reads_the_saved_state_in_utc() -> None:
    """Case 01 finished 00:29 CEST on 14 September: 22:29 UTC on the 13th, said so."""
    final = {"run_integrity": {"generated_at": "2026-09-14T00:29:42+02:00"}}
    assert completed_on(final) == "Completed 13 September 2026, 22:29 UTC"


def test_no_recorded_completion_no_date() -> None:
    """Nothing saved, nothing claimed."""
    assert completed_on({}) is None
    assert completed_on({"run_integrity": {"generated_at": "not a time"}}) is None
