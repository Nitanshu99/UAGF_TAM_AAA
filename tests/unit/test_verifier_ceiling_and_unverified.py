"""Fix 20 — the Verifier's own ceiling, and a fallback critique recorded honestly.

P6: both delivered documents (and T15) were critiqued by the deterministic
fallback after the Verifier's LLM call timed out, and all three recorded
``accept`` — a quality gate that did not run, indistinguishable in the state
from one that ran and passed.  P8: 5 of 21 Verifier calls errored against a
120 s ceiling the same provider was answering past in the same run.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aaa.agents.tier1.phases.verification.finish_phase import _finish_phase
from aaa.agents.tier1.phases.verification.logger import _VERDICT_ORDER, _worse
from aaa.agents.tier1.phases.verification.unadmitted import (
    clear_unadmitted_insufficiency,
    gate_on_unadmitted,
)
from aaa.agents.tier1.verifier.fallback import fallback_critique
from aaa.agents.tier1.verifier.verdicts import (
    MAX_RERUNS,
    UNVERIFIED,
    decide_fallback_verdict,
    decide_verdict,
)
from aaa.platform.model_registry.timeouts import VERIFIER_TIMEOUT_SECONDS, resolve_timeout

T09 = "T09_model_card"
T18 = "T18_audit_report"


# ── the ceiling ──────────────────────────────────────────────────────────────

def test_the_verifier_outranks_the_phase_agents_ceiling():
    from aaa.platform.flex_retry import DEFAULT_TIMEOUT_SECONDS
    assert resolve_timeout("Verifier") > DEFAULT_TIMEOUT_SECONDS


def test_the_ceiling_clears_the_slowest_call_the_provider_actually_completed():
    """The run's slowest successful Verifier call took 240.3 s."""
    assert VERIFIER_TIMEOUT_SECONDS > 240.3


def test_a_phase_agent_takes_the_platform_default():
    assert resolve_timeout("DataAuditor") is None
    assert resolve_timeout("ModelValidator") is None


def test_an_explicit_override_wins():
    assert resolve_timeout("Verifier", 42.0) == 42.0
    assert resolve_timeout("DataAuditor", 42.0) == 42.0


def test_the_verifier_carries_its_ceiling_into_the_litellm_call():
    from aaa.agents.tier1.verifier import Verifier
    assert Verifier()._litellm_kwargs()["timeout"] == VERIFIER_TIMEOUT_SECONDS


def test_an_agent_without_a_ceiling_sends_no_timeout_key():
    from aaa.agents.tier2.data_auditor import DataAuditor
    from aaa.platform.evidence import EvidenceStore
    assert "timeout" not in DataAuditor(EvidenceStore())._litellm_kwargs()


def test_flex_acompletion_honours_a_caller_supplied_ceiling():
    """The wrapper used to overwrite whatever the caller asked for."""
    import sys
    import types

    seen: dict[str, Any] = {}

    async def _fake(**kwargs):
        seen.update(kwargs)
        return "resp"

    stub = types.ModuleType("litellm")
    stub.acompletion = _fake  # type: ignore[attr-defined]
    real = sys.modules.get("litellm")
    sys.modules["litellm"] = stub
    try:
        from aaa.platform.flex_retry import flex_acompletion
        asyncio.run(flex_acompletion(model="m", messages=[], timeout=300.0))
        assert seen["timeout"] == 300.0
        seen.clear()
        asyncio.run(flex_acompletion(model="m", messages=[]))
        from aaa.platform.flex_retry import DEFAULT_TIMEOUT_SECONDS
        assert seen["timeout"] == DEFAULT_TIMEOUT_SECONDS
    finally:
        if real is not None:
            sys.modules["litellm"] = real
        else:
            del sys.modules["litellm"]


# ── the honest record ────────────────────────────────────────────────────────

class _Agent:
    def prompt_metadata(self, name, fallback):  # noqa: ARG002
        return {"prompt": name, "fallback": fallback}


def test_a_clean_structural_check_is_not_an_acceptance():
    crit = fallback_critique(_Agent(), "P6", T18, {"executive_summary": "x"},
                             ["minio://e"], 0, "minio://a", reason="Timeout")
    assert crit["verdict"] == UNVERIFIED
    assert crit["llm_fallback_mode"] is True
    assert crit["rerun_required"] is False
    assert any("unverified, not accepted" in n for n in crit["notes"])
    assert "Timeout" in crit["unverified_reason"]


def test_a_structural_issue_still_runs_the_rerun_ladder():
    """An empty artefact is empty whether or not a model read it."""
    crit = fallback_critique(_Agent(), "P3", T09, {}, ["minio://e"], 0, "minio://a")
    assert crit["verdict"] == "rerun"
    assert crit["rerun_required"] is True


def test_the_ladder_escalates_once_the_reruns_are_spent():
    assert decide_fallback_verdict(["empty"], MAX_RERUNS) == "escalate_hitl"
    assert decide_fallback_verdict(["empty"], 0) == "rerun"


def test_the_llm_ladder_is_untouched():
    """Only the deterministic path changed; a real critique still accepts."""
    assert decide_verdict([], [], 0) == "accept"
    assert decide_verdict([], ["a note"], 0) == "accept_with_notes"


def test_a_verifier_crash_records_unverified_not_accept_with_notes():
    from aaa.agents.tier1.phases.verification.critique_artefact import _critique_artefact

    class _Boom:
        async def process(self, message):  # noqa: ARG002
            raise RuntimeError("provider down")

    class _Agent2:
        store = None

    state: dict = {"verifier_critiques": {}, "phase_artefacts": {}}
    verdict = asyncio.run(_critique_artefact(
        _Boom(), _Agent2(), state, T09, ["Art.13"], "Phase 3", 0.9,
        phase_id="P3", evidence_uris=[], rerun_count=0, declaration_summary={}))
    assert verdict == UNVERIFIED
    assert state["verifier_critiques"][T09]["verdict"] == UNVERIFIED


# ── the consequences ─────────────────────────────────────────────────────────

def test_unverified_is_not_admitted_anywhere():
    from aaa.agents.tier1.phases.compliance_matrix import _ADMITTED_VERDICTS as MATRIX
    from aaa.tools.completeness_score import _ADMITTED_VERDICTS as COMPLETENESS
    from aaa.tools.regulatory_coverage import _ADMITTED_VERDICTS as COVERAGE
    for admitted in (MATRIX, COMPLETENESS, COVERAGE):
        assert UNVERIFIED not in admitted


def test_unverified_outranks_admission_but_not_a_rerun():
    """A rerun re-critiques both artefacts, which is the free Verifier retry."""
    assert _VERDICT_ORDER.index(UNVERIFIED) > _VERDICT_ORDER.index("accept_with_notes")
    assert _VERDICT_ORDER.index(UNVERIFIED) < _VERDICT_ORDER.index("rerun")
    assert _worse(UNVERIFIED, "rerun") == "rerun"
    assert _worse(UNVERIFIED, "accept") == UNVERIFIED


def test_an_unverified_phase_routes_to_human_review_with_its_own_reason():
    state: dict = {}
    _finish_phase(state, UNVERIFIED, 0, "Phase 6 ReportArchitect", 0.0)
    assert state["hitl_required"] is True
    assert "critique did not run" in state["hitl_reason"]


def test_an_unverified_artefact_reaches_the_review_packet():
    from aaa.tools.hitl_review import _HITL_VERDICTS
    assert UNVERIFIED in _HITL_VERDICTS


def _unverified_state(tid: str) -> dict:
    return {"verifier_critiques": {tid: {"verdict": UNVERIFIED,
                                         "unverified_reason": "Timeout"}}}


def test_an_unverified_artefacts_articles_are_unevidenced_not_absent():
    state = _unverified_state(T09)
    newly = gate_on_unadmitted(state, {T09: ["Art.13", "Art.15"]},
                               phase_id="P3", phase_label="Phase 3")
    assert newly == ["Art.13", "Art.15"]
    assert state["insufficient_evidence_articles"] == ["Art.13", "Art.15"]
    assert state["unadmitted_artefacts"][0]["reason"] == "Timeout"


def test_the_article_gate_yields_insufficient_evidence_in_the_matrix():
    from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import _article_verdict
    assert _article_verdict("Art.13", [], set(), {"Art.13"}) == "INSUFFICIENT_EVIDENCE"


def test_a_report_template_is_flagged_without_unevidencing_its_article():
    state = _unverified_state(T18)
    newly = gate_on_unadmitted(state, {T18: ["Art.17"]},
                               phase_id="P6", phase_label="Phase 6")
    assert newly == []
    assert state["unadmitted_artefacts"][0]["template_id"] == T18
    assert state["blocking_findings"][0]["eu_ai_act_articles"] == []
    # The finding names the artefact, its verdict and the reason (Q1): a reader
    # must be able to act on it without opening the critique.
    assert "T18_audit_report (unverified — Timeout)" in (
        state["blocking_findings"][0]["description"])


def test_a_verified_phase_records_nothing():
    state = {"verifier_critiques": {T09: {"verdict": "accept_with_notes"}}}
    assert gate_on_unadmitted(state, {T09: ["Art.13"]},
                              phase_id="P3", phase_label="Phase 3") == []
    assert "unadmitted_artefacts" not in state
    assert "blocking_findings" not in state


def test_an_artefact_verified_on_the_rerun_leaves_no_stale_insufficiency():
    """The gate reads the critiques as they finally stand, not attempt 1's."""
    state = _unverified_state(T09)
    state["verifier_critiques"][T09]["verdict"] = "accept"  # the rerun succeeded
    assert gate_on_unadmitted(state, {T09: ["Art.13"]},
                              phase_id="P3", phase_label="Phase 3") == []


# ── the gate is not one-way ──────────────────────────────────────────────────

def test_a_human_who_admits_the_artefact_releases_its_articles():
    state = _unverified_state(T09)
    gate_on_unadmitted(state, {T09: ["Art.13"]}, phase_id="P3", phase_label="Phase 3")
    state["verifier_critiques"][T09]["verdict"] = "accept_with_notes"
    assert clear_unadmitted_insufficiency(state) == ["Art.13"]
    assert state["insufficient_evidence_articles"] == []
    assert state["unadmitted_artefacts"] == []


def test_an_article_another_unverified_artefact_still_names_is_held():
    state = _unverified_state(T09)
    state["verifier_critiques"]["T10_explainability_report"] = {"verdict": UNVERIFIED}
    gate_on_unadmitted(state, {T09: ["Art.13"], "T10_explainability_report": ["Art.13"]},
                       phase_id="P3", phase_label="Phase 3")
    state["verifier_critiques"][T09]["verdict"] = "accept"
    assert clear_unadmitted_insufficiency(state) == []
    assert state["insufficient_evidence_articles"] == ["Art.13"]


def test_an_article_a_low_confidence_phase_contributed_is_held():
    state = _unverified_state(T09)
    gate_on_unadmitted(state, {T09: ["Art.13"]}, phase_id="P3", phase_label="Phase 3")
    state["low_confidence_phases"] = [{"phase_id": "P3", "articles": ["Art.13"]}]
    state["verifier_critiques"][T09]["verdict"] = "accept"
    assert clear_unadmitted_insufficiency(state) == []


@pytest.mark.parametrize("state", [{}, {"unadmitted_artefacts": []}])
def test_releasing_nothing_is_a_no_op(state):
    assert clear_unadmitted_insufficiency(dict(state)) == []
