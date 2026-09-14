"""Prompt snapshot tests: the verifier system-prompt content contract."""
from __future__ import annotations

from aaa.agents.tier1.verifier import _SYSTEM_PROMPT


def test_system_prompt_contains_required_content():
    for phrase in ("factual_accuracy", "completeness", "evidence_linkage",
                   "regulatory citation", "materiality", "materiality_rationale",
                   "materiality_assessments", "ESCALATE_HITL"):
        assert phrase.lower() in _SYSTEM_PROMPT.lower()


def test_system_prompt_forbids_hidden_chain_of_thought_output():
    prompt = _SYSTEM_PROMPT.lower()
    assert "do not emit hidden chain-of-thought" in prompt
    assert "scratchpad" in prompt
