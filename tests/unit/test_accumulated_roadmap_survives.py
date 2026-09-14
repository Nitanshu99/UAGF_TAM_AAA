"""All CGSA roadmap rows reach state, and re-runs still de-duplicate.

Every case-06 run ended with one remediation item in state out of 36: the findings
de-duplication keyed roadmap rows on fields they do not have (T-20260913-030).
"""
from __future__ import annotations

from aaa.agents.tier1.phases.agent_runner.apply_delta import _apply_delta
from aaa.agents.tier1.phases.agent_runner.dedup_accumulated import _dedup_accumulated

ROADMAP = [{"rank": i, "control_id": f"C{i:02d}", "gap_severity": "high"} for i in range(1, 37)]


def _state() -> dict:
    return {"phase_artefacts": {}, "remediation_roadmap": [], "blocking_findings": []}


def test_every_roadmap_row_survives_the_merge() -> None:
    """36 in, 36 in state."""
    state = _state()
    _apply_delta(state, {"remediation_roadmap": ROADMAP})
    assert len(state["remediation_roadmap"]) == 36


def test_a_rerun_does_not_duplicate_the_roadmap() -> None:
    """The same delta twice is still 36 rows."""
    state = _state()
    _apply_delta(state, {"remediation_roadmap": ROADMAP})
    _apply_delta(state, {"remediation_roadmap": ROADMAP})
    assert [r["control_id"] for r in state["remediation_roadmap"]] == [r["control_id"] for r in ROADMAP]


def test_findings_still_deduplicate_as_before() -> None:
    """The re-run duplicate the original fix was for is still removed."""
    finding = {"finding_id": "P5-CGSA-COUNT", "description": "x", "source_phase": "P5"}
    assert _dedup_accumulated([finding, dict(finding), dict(finding)], "blocking_findings") == [finding]


def test_items_with_no_identity_only_match_identical_items() -> None:
    """Different anonymous dicts are kept; identical ones collapse."""
    a, b = {"note": "one"}, {"note": "two"}
    assert _dedup_accumulated([a, b, dict(a)], "anything") == [a, b]
