"""T-20260914-015: only a defect in the artefact bears on its admission.

Case 01's T09 quoted the provider's wrong Art. 10(5) claim and case 05's T06 stated
undocumented collection processes; both were escalated, their articles unassessed.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.rerun_context import build_rerun_context
from aaa.agents.tier1.verifier.issues import _normalise_issues, material_non_conformity
from aaa.agents.tier1.verifier.verdict_codes import _map_llm_verdict

_GAP = {"severity": "critical", "materiality": "material", "issue_type": "evidence_gap",
        "description": "No document states how the data was collected."}
_CLAIM = {"severity": "critical", "materiality": "material",
          "issue_type": "provider_nonconformity",
          "description": "The quoted Art. 10(5) basis for age is legally wrong."}
_DEFECT = {"severity": "major", "materiality": "material", "issue_type": "artefact_defect",
           "description": "The narrative contradicts the verification map."}


def test_types_are_kept_and_unknown_is_a_defect() -> None:
    """Provider types survive; nonsense or absence reads as a defect."""
    issues = _normalise_issues([_GAP, {**_CLAIM, "issue_type": "weather"}, {"description": "x"}])
    assert [i["issue_type"] for i in issues] == ["evidence_gap", "artefact_defect",
                                                 "artefact_defect"]


def test_provider_issues_neither_block_admission_nor_force_a_rejection() -> None:
    """Material provider findings admit; the same materiality on a defect escalates."""
    provider = _normalise_issues([_GAP, _CLAIM])
    assert material_non_conformity(provider) is None
    assert _map_llm_verdict("ESCALATE_HITL", provider, [], 0, {"factual_accuracy": 2}) \
        == "accept_with_notes"
    assert _map_llm_verdict("ESCALATE_HITL", provider, [], 0, {"factual_accuracy": 0}) \
        == "escalate_hitl"
    mixed = _normalise_issues([_GAP, _DEFECT])
    assert _map_llm_verdict("ACCEPT_WITH_OBSERVATIONS", mixed, [], 0) == "escalate_hitl"


def test_a_rerun_is_told_only_what_it_can_fix() -> None:
    """The agent's rerun context carries the defect, not the provider's gap."""
    state = {"verifier_critiques": {"T06": {"verdict": "rerun",
                                            "issues": _normalise_issues([_GAP, _DEFECT])}}}
    issues = build_rerun_context(state, ["T06"], 1)["rejected_artefacts"][0]["issues"]
    assert [i["issue_type"] for i in issues] == ["artefact_defect"]


def test_the_verifier_prompt_defers_to_measured_decisions() -> None:
    """Case 06: an upper bound of 0.93 was read as below four-fifths, and missing model
    access as a non-conformity; the loaded Verifier prompt now rules out both."""
    from aaa.platform.prompt_registry.extract_agent_section import load_prompt

    prompt = load_prompt("verifier")
    assert "MEASURED DECISIONS" in prompt and "bound is below 0.8" in prompt
    assert "ACCESS IS NOT CONFORMITY" in prompt


def test_agent_prompts_carry_no_retired_threshold() -> None:
    """Output Fairness and the L-branch are told the rules the code applies (T-20260914-035)."""
    from aaa.platform.prompt_registry.extract_agent_section import load_prompt

    fairness, l_branch = load_prompt("phase4_output"), load_prompt("uagf_tam_l")
    for retired in ("difference > 0.10", "ratio < 0.80", "threshold 0.80", "> 0.5%"):
        assert retired not in fairness
    for retired in ("Relevancy < 0.80", "Faithfulness < 0.85", "Recall < 0.75", "< 0.90"):
        assert retired not in l_branch
    assert "interval" in fairness and "declared target" in l_branch


def test_an_explained_absence_is_a_gap_not_a_defect() -> None:
    """Case 04: T08's unnamed declared category and T03's uncorroborated §8 were escalated."""
    from aaa.platform.prompt_registry.extract_agent_section import load_prompt

    prompt = load_prompt("verifier")
    assert "absence the artefact's own narrative or rationale explains" in prompt
    assert "says it has not" in prompt and "corroborated" in prompt
