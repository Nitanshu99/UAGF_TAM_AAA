"""Fix 19 — a tier-3 spawn extends a tier-2 template without displacing it (P5).

The post-fix run stored ``T08`` under ``Privacy/`` and ``T11`` under
``CyberSecurity/`` on the phase's own keys, so the Phase 2 and Phase 3 artefacts
became unreadable while their critiques (``escalate_hitl`` / ``rerun``) stayed
attached to the template ids.  These tests pin the key space, the delta
boundary that enforces it, the dispatch fields the spawns were never given, and
the two verdicts a starved spawn used to fabricate.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aaa.agents.tier1.phases.agent_runner import _apply_delta, run_agent_on_state
from aaa.agents.tier3.cyber_agent.t11_update import update_t11
from aaa.agents.tier3.cyber_agent.verdict import derive_verdict
from aaa.agents.tier3.privacy_agent.eval_data import load_scan_frame
from aaa.agents.tier3.privacy_agent.t08_update import update_t08
from aaa.platform.state.artefact_keys import (
    SPAWN_CYBER,
    SPAWN_PRIVACY,
    base_template_id,
    is_namespaced,
    namespace_artefacts,
    namespaced_key,
)

T08 = "T08_special_category_data_log"
T11 = "T11_robustness_report"


# ── the key space ────────────────────────────────────────────────────────────

def test_a_spawn_key_names_the_template_and_the_spawn():
    assert namespaced_key(T11, SPAWN_CYBER) == "T11_robustness_report@Cyber"
    assert is_namespaced(namespaced_key(T11, SPAWN_CYBER))
    assert base_template_id(namespaced_key(T11, SPAWN_CYBER)) == T11


def test_a_plain_template_id_is_its_own_base():
    assert not is_namespaced(T11)
    assert base_template_id(T11) == T11


def test_namespacing_is_idempotent():
    once = namespaced_key(T11, SPAWN_CYBER)
    assert namespaced_key(once, SPAWN_CYBER) == once


def test_an_empty_spawn_never_produces_a_dangling_separator():
    assert namespaced_key(T11, "") == T11


def test_namespacing_a_block_keeps_each_refs_own_template_id():
    out = namespace_artefacts({T11: {"uri": "minio://x", "template_id": T11}}, SPAWN_CYBER)
    assert list(out) == ["T11_robustness_report@Cyber"]
    assert out["T11_robustness_report@Cyber"]["template_id"] == T11


def test_a_ref_without_a_template_id_gains_the_one_its_key_named():
    out = namespace_artefacts({T08: {"uri": "minio://x"}}, SPAWN_PRIVACY)
    assert out["T08_special_category_data_log@Privacy"]["template_id"] == T08


# ── the delta boundary ───────────────────────────────────────────────────────

def _state() -> dict:
    return {"phase_artefacts": {
        T11: {"uri": "minio://eng/phase_3/T11.json", "template_id": T11}}}


def test_a_spawn_delta_cannot_land_on_the_phases_key():
    state = _state()
    _apply_delta(state, {"phase_artefacts": {
        T11: {"uri": "minio://eng/CyberSecurity/T11.json"}}}, SPAWN_CYBER)
    assert state["phase_artefacts"][T11]["uri"] == "minio://eng/phase_3/T11.json"
    assert state["phase_artefacts"]["T11_robustness_report@Cyber"]["uri"].endswith(
        "CyberSecurity/T11.json")


def test_a_phase_rerun_still_replaces_its_own_artefact():
    """Without a spawn the merge is unchanged — a rerun must overwrite."""
    state = _state()
    _apply_delta(state, {"phase_artefacts": {
        T11: {"uri": "minio://eng/phase_3/T11_v2.json"}}})
    assert state["phase_artefacts"][T11]["uri"].endswith("T11_v2.json")
    assert len(state["phase_artefacts"]) == 1


# ── the dispatch the spawns were never given ─────────────────────────────────

class _EchoAgent:
    """Records the dispatch it was handed and emits a bare-keyed delta."""

    def __init__(self) -> None:
        self.seen: dict[str, Any] = {}

    async def process(self, message: Any) -> dict:
        self.seen = dict(message.get("declaration_summary") or {})
        return {"declaration_verification_delta": {
            "phase_artefacts": {T11: {"uri": "minio://eng/CyberSecurity/T11.json"}}}}


def test_the_runner_namespaces_whatever_the_spawn_emits():
    """The guarantee is the runner's, not the agent's good behaviour."""
    agent, state = _EchoAgent(), _state()
    asyncio.run(run_agent_on_state(agent, {"phase_id": "Cyber", "declaration_summary": {}},
                                   state, timeout=5, spawn=SPAWN_CYBER))
    assert "T11_robustness_report@Cyber" in state["phase_artefacts"]
    assert state["phase_artefacts"][T11]["uri"].endswith("phase_3/T11.json")


def test_the_cyber_dispatch_carries_the_artefact_it_is_told_to_extend():
    from aaa.agents.tier1.phases.phase_runners import run_cyber_subagent
    agent, state = _EchoAgent(), _state()
    state.update({"engagement_id": "eng", "modality": "tabular",
                  "client_submission": {"stage_b": {"model_artifact_uri": "minio://m"}}})
    asyncio.run(run_cyber_subagent(agent, state))
    assert T11 in agent.seen["phase_artefacts"]
    assert agent.seen["stage_b"]["model_artifact_uri"] == "minio://m"


def test_the_privacy_dispatch_carries_stage_b_for_the_pii_deep_dive():
    from aaa.agents.tier1.phases.phase_runners import run_privacy_subagent
    agent, state = _EchoAgent(), _state()
    state.update({"engagement_id": "eng", "modality": "tabular",
                  "client_submission": {"stage_b": {"evaluation_dataset_uri": "minio://e"}}})
    asyncio.run(run_privacy_subagent(agent, state))
    assert agent.seen["stage_b"]["evaluation_dataset_uri"] == "minio://e"
    assert agent.seen["phase_artefacts"] is state["phase_artefacts"]


# ── the two fabrications a starved spawn produced ────────────────────────────

def test_no_probe_is_not_a_pass():
    """The 1.0 seed made an empty probe list derive PASS on no measurement."""
    assert derive_verdict([], None) == "NOT_TESTED"
    assert derive_verdict([{"probe_name": "ran but measured nothing"}], None) == "NOT_TESTED"


def test_the_probes_own_verdict_decides():
    """The robustness probe's verdict (T-20260914-007), not an accuracy floor."""
    measured = [{"adversarial_accuracy": 0.5}]
    assert derive_verdict(measured, None, "PASS") == "PASS"
    assert derive_verdict(measured, None, "FAIL") == "FAIL"
    assert derive_verdict(measured, None) == "PASS_WITH_OBSERVATIONS"  # measured, not judged


def test_an_overstated_injection_declaration_is_decisive_without_a_probe():
    """40 of 100 attacks succeeding cannot support a declared 0.99 detection rate."""
    suite = {"vulnerability_rate": 0.4, "total_probes": 100, "successful_attacks": 40}
    assert derive_verdict([], suite, None, {"prompt_injection_detection_rate": 0.99}) == "FAIL"
    assert derive_verdict([], suite) == "PASS_WITH_OBSERVATIONS"


def test_t11_declares_when_the_specialist_probe_did_not_run():
    out = update_t11({}, "eng", "tabular", [], None, extended=False,
                     probe_skipped="No model or labels supplied.")
    assert "did not run" in out["skipped_reason"]
    assert "no Phase 3" in out["art15_compliance_notes"]
    assert out["overall_robustness_verdict"] == "NOT_TESTED"


def test_t11_stays_silent_on_the_healthy_path():
    out = update_t11({"probes": []}, "eng", "tabular",
                     [{"adversarial_accuracy": 0.9}], None)
    assert "skipped_reason" not in out
    assert "no Phase 3" not in out["art15_compliance_notes"]
    assert out["min_adversarial_accuracy"] == 0.9


def test_t08_distinguishes_a_clean_scan_from_a_scan_that_did_not_run():
    ran, _ = update_t08({}, "eng", {"special_categories_found": [],
                                    "analyser_engine": "presidio"})
    skipped, _ = update_t08({}, "eng", {}, "no evaluation dataset URI was supplied")
    assert "did not run" not in ran["compliance_narrative"]
    assert "re-scanned with presidio" in ran["compliance_narrative"]
    assert "did not run" in skipped["compliance_narrative"]
    assert "no independent scan evidence" in skipped["compliance_narrative"]


def test_t08_never_drops_phase_2s_categories():
    out, merged = update_t08(
        {"special_categories_detected": ["racial_or_ethnic_origin"]}, "eng", {},
        "no evaluation dataset URI was supplied")
    assert out["special_categories_detected"] == ["racial_or_ethnic_origin"]
    assert merged == ["racial_or_ethnic_origin"]


# ── the deep-dive's dataset ──────────────────────────────────────────────────

def test_the_deep_dive_says_why_it_has_no_frame():
    frame, reason = load_scan_frame(object(), {"stage_b": {}})
    assert frame is None
    assert "no evaluation or training dataset URI" in reason


def test_the_deep_dive_prefers_the_evaluation_set():
    seen: list[str] = []

    class _Store:
        pass

    def _fake(uri, store, kind):  # noqa: ARG001
        seen.append(uri)
        return "frame"

    import aaa.agents.tier3.privacy_agent.eval_data as mod
    real = mod.load_artifact_from_uri
    mod.load_artifact_from_uri = _fake
    try:
        frame, reason = load_scan_frame(_Store(), {"stage_b": {
            "training_dataset_uri": "minio://train.csv",
            "evaluation_dataset_uri": "minio://eval.csv"}})
    finally:
        mod.load_artifact_from_uri = real
    assert frame == "frame" and reason == ""
    assert seen == ["minio://eval.csv"]


def test_an_unloadable_dataset_is_a_reason_not_an_exception():
    from aaa.platform.artifact_loader import ArtifactUnavailable

    def _raise(uri, store, kind):  # noqa: ARG001
        raise ArtifactUnavailable(uri, kind, "not found")

    import aaa.agents.tier3.privacy_agent.eval_data as mod
    real = mod.load_artifact_from_uri
    mod.load_artifact_from_uri = _raise
    try:
        frame, reason = load_scan_frame(object(), {
            "stage_b": {"evaluation_dataset_uri": "minio://gone.csv"}})
    finally:
        mod.load_artifact_from_uri = real
    assert frame is None
    assert "could not be loaded" in reason


# ── the consumers that must read the base template id ────────────────────────

def test_the_report_embeds_the_spawns_artefact_under_its_real_template_id():
    from aaa.agents.tier2.report_architect.t18.sections import embedded_artefacts
    out = embedded_artefacts({"phase_artefacts": {
        "T11_robustness_report@Cyber": {"uri": "minio://x", "template_id": T11}}})
    assert out["T11_robustness_report@Cyber"]["template_id"] == T11


def test_a_spawn_artefact_reaches_hitl_under_the_templates_phase():
    from aaa.tools.hitl_review.case_entry import _case_entry
    case = _case_entry({"phase_artefacts": {}, "verifier_critiques": {}},
                       "T08_special_category_data_log@Privacy")
    assert case["phase"] == "P2 Data Governance"


@pytest.mark.parametrize("tid", [T08, T11])
def test_the_phase_lookup_is_unchanged_for_plain_ids(tid):
    from aaa.tools.hitl_review.case_entry import _case_entry
    case = _case_entry({"phase_artefacts": {}, "verifier_critiques": {}}, tid)
    assert case["phase"] != "unknown"
