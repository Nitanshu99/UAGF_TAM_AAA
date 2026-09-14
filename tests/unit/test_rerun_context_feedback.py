"""Finding F2 — a verifier-ordered rerun must carry the critique that ordered it.

In the assessed run, calls #003 and #008 (attempt 1 and the rerun) had
byte-identical user messages — SHA-256 `5ebf976e2a028611` both times — with
`rerun_context: null` in each.  The Verifier's `critical` finding, its
localisation to `composition.num_instances` and its explicit recommendation
were all discarded, and the phase re-sampled the same prompt.
"""
from __future__ import annotations

import asyncio
import hashlib
import json

import pytest

from aaa.agents.tier1.phases.verification.rerun_context import build_rerun_context
from aaa.platform.prompt_registry import load_prompt

PHASE_PROMPTS = ("phase1_scope", "phase2_data", "phase3_model",
                 "phase4_output", "phase5_governance")

#: The critique the Verifier actually returned at call #005.
_CALL_005_ISSUE = {
    "field": "composition.num_instances",
    "severity": "critical",
    "materiality": "material",
    "description": "Field value is 0 but artefact.description and "
                   "declaration_summary both state 1000 instances.",
    "recommendation": "Set num_instances = 1000.",
}


def _state_after_rerun_verdict() -> dict:
    return {"verifier_critiques": {
        "T06_datasheet_for_datasets": {
            "verdict": "rerun", "issues": [_CALL_005_ISSUE],
            "notes": ["Phase 2 complete. confidence=0.30"],
            "scores": {"internal_consistency": 0},
        },
        "T07_data_quality_report": {"verdict": "accept_with_notes", "issues": []},
    }}


def test_rerun_context_carries_only_the_rejected_artefacts():
    ctx = build_rerun_context(
        _state_after_rerun_verdict(),
        ["T06_datasheet_for_datasets", "T07_data_quality_report"],
        attempt=1)

    assert ctx["reason"] == "verifier_rerun"
    assert ctx["attempt"] == 1
    rejected = ctx["rejected_artefacts"]
    assert [r["template_id"] for r in rejected] == ["T06_datasheet_for_datasets"], (
        "an accepted artefact must not be sent back for rework")
    assert rejected[0]["issues"][0]["recommendation"] == "Set num_instances = 1000."


def test_rerun_context_is_empty_when_nothing_was_rejected():
    state = {"verifier_critiques": {"T06": {"verdict": "accept", "issues": []}}}
    assert build_rerun_context(state, ["T06"], attempt=1)["rejected_artefacts"] == []


@pytest.mark.parametrize("name", PHASE_PROMPTS)
def test_phase_prompts_tell_the_agent_what_to_do_with_a_rerun_context(name):
    prompt = load_prompt(name)
    assert "## RERUN PROTOCOL" in prompt
    assert "rerun_context.rejected_artefacts" in prompt


def test_rerun_dispatch_differs_from_the_first_attempt(monkeypatch):
    """The regression the assessment asked for: attempt 2 must not be a re-roll."""
    import importlib
    mod = importlib.import_module(
        "aaa.agents.tier1.phases.verification.run_phase_with_verification")

    seen: list[str] = []

    class _Agent:
        name = "DataAuditor"
        store = None

    async def _fake_run(agent, dispatch, state, timeout=180):
        seen.append(hashlib.sha256(
            json.dumps(dispatch, sort_keys=True, default=str).encode()).hexdigest())
        return {"confidence": 0.3, "declaration_verification_delta": {}}, state

    verdicts = iter(["rerun", "accept"])

    async def _fake_verify(verifier, agent, dispatch, state, tid_articles,
                           phase_label, confidence, rerun_count):
        # The critiques and the returned worst verdict have to agree: since fix
        # 32 the loop reads the critiques per artefact rather than trusting the
        # aggregate, and the real `_verify_artefacts` derives one from the other.
        verdict = next(verdicts)
        critiques = _state_after_rerun_verdict()["verifier_critiques"]
        critiques["T06_datasheet_for_datasets"]["verdict"] = verdict
        state["verifier_critiques"] = critiques
        return verdict

    monkeypatch.setattr(mod, "run_agent_on_state", _fake_run)
    monkeypatch.setattr(mod, "_verify_artefacts", _fake_verify)
    monkeypatch.setattr(mod, "_get_verifier", lambda _rag=None: object())

    dispatch = {"phase_id": "P2", "task_brief": "Execute Phase 2",
                "evidence_uris": [], "output_contract": "T06",
                "declaration_summary": {}}
    asyncio.run(mod.run_phase_with_verification(
        _Agent(), dispatch, {"verifier_critiques": {}},
        {"T06_datasheet_for_datasets": ["Art.10"]}, "Phase 2"))

    assert len(seen) == 2, "expected an initial attempt and one rerun"
    assert seen[0] != seen[1], (
        "the rerun dispatch is byte-identical to the first attempt (F2)")
    assert dispatch["rerun_context"]["rejected_artefacts"][0]["issues"][0][
        "recommendation"] == "Set num_instances = 1000."


def test_react_expansion_does_not_clobber_the_critique():
    """The retrieval loop used to overwrite rerun_context with its own bookkeeping."""
    from aaa.tools.evidence_retrieval import acompletion_json_react

    captured: list[dict] = []

    class _Agent:
        name = "Fake"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):
            captured.append(payload)
            type(self).calls += 1
            if type(self).calls == 1:
                return {"retrieval_plan": {"regulatory_queries": ["Article 10"],
                                           "client_doc_queries": []}}
            return {"done": True}

    class _Rag:
        def search(self, query, top_k=3):
            return [{"source_uri": "euaiact://Article_10"}]

    critique = {"reason": "verifier_rerun", "attempt": 1, "rejected_artefacts": [1]}
    asyncio.run(acompletion_json_react(
        _Agent(), "phase2_data", {"rerun_context": critique},
        rag=_Rag(), engagement_id="", rounds=1))

    assert captured[-1]["rerun_context"] == critique, (
        "retrieval-plan expansion overwrote the Verifier critique")
    assert captured[-1]["retrieval_expansion"]["round"] == 1
