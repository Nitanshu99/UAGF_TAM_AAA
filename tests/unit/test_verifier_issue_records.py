"""The Verifier's issue objects, end to end (M12, M17).

``PROMPT.md`` asks for ``severity``, ``field``, ``description``,
``recommendation``, ``materiality`` and ``materiality_rationale`` on every issue.
The parse kept ``description`` and dropped the rest, which cost two things: the
rerun carried no recommendation, and ``_blocking_issues`` — which filters for
dicts with a blocking severity to build what the Orchestrator sees — matched
nothing at all.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.phase_outcome import _blocking_issues
from aaa.agents.tier1.phases.verification.rerun_context import build_rerun_context
from aaa.agents.tier1.phases.verification.unadmitted import _reason
from aaa.agents.tier1.verifier.issues import _normalise_issues, issue_text
from aaa.agents.tier1.verifier.result import _result

#: Call #007's issue, verbatim in shape.
_CRITICAL = {
    "severity": "critical", "field": "binding_statement",
    "description": "The Art. 43 rationale contradicts the recorded inputs.",
    "recommendation": "Re-derive the procedure: Annex VII, not Annex VI.",
    "materiality": "material",
    "materiality_rationale": "A regulator would question the conformity route.",
}


class _Agent:
    def prompt_metadata(self, *_a, **_k):
        return {}


def test_every_prompt_defined_field_survives_the_parse():
    issue = _normalise_issues([_CRITICAL])[0]
    # An untyped issue is read as a defect in the artefact (T-20260914-015).
    assert issue == {**_CRITICAL, "issue_type": "artefact_defect"}


def test_a_bare_string_still_parses():
    assert _normalise_issues(["just a sentence"]) == [
        {"description": "just a sentence", "issue_type": "artefact_defect"}]


def test_an_issue_with_no_text_is_dropped():
    assert _normalise_issues([{"severity": "minor"}, None, ""]) == []


def test_a_non_list_is_empty():
    assert _normalise_issues("not a list") == []


def test_issue_text_renders_both_shapes():
    assert issue_text(_CRITICAL) == _CRITICAL["description"]
    assert issue_text("plain") == "plain"
    assert issue_text({"field": "only_a_field"}) == "only_a_field"


def test_the_rerun_carries_the_recommendation_it_was_given():
    """The rerun is *verify, then re-run with feedback*; the fix is the feedback."""
    state = {"verifier_critiques": {"T05": {
        "verdict": "rerun", "issues": _normalise_issues([_CRITICAL]), "notes": [],
        "scores": {"factual_accuracy": 0}}}}
    rejected = build_rerun_context(state, ["T05"], 1)["rejected_artefacts"][0]
    assert rejected["issues"][0]["recommendation"] == _CRITICAL["recommendation"]
    assert rejected["issues"][0]["severity"] == "critical"


def test_the_orchestrator_sees_a_critical_issue():
    """`blocking_issues` was [] on all 37 occurrences of the assessed run."""
    seen = _blocking_issues({"issues": _normalise_issues([_CRITICAL])})
    assert len(seen) == 1
    assert seen[0]["severity"] == "critical"
    assert seen[0]["field"] == "binding_statement"
    assert seen[0]["recommendation"].startswith("Re-derive the procedure")


def test_a_minor_issue_is_not_blocking():
    minor = {**_CRITICAL, "severity": "minor"}
    assert _blocking_issues({"issues": _normalise_issues([minor])}) == []


def test_the_unadmitted_reason_reads_descriptions_not_dict_reprs():
    """`_reason` renders the critique in the Verifier's own words."""
    reason = _reason({"issues": _normalise_issues([_CRITICAL])}, "escalate_hitl")
    assert reason == _CRITICAL["description"]
    assert "severity" not in reason


def test_the_stored_critique_keeps_the_records():
    stored = _result("P1", "T05", {"verdict": "RERUN", "issues": [_CRITICAL]},
                     rerun_count=0, agent=_Agent())
    assert stored["issues"][0]["materiality"] == "material"
    assert stored["verdict"] == "rerun"
