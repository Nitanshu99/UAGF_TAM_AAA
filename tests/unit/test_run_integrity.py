"""Unit tests for the run-integrity block (fix F2, finding S3)."""
from __future__ import annotations

import json
from pathlib import Path

from aaa.platform.state.run_integrity import (
    RUN_INTEGRITY_KEY,
    STUB_SHA,
    build_run_integrity,
    degraded_phases,
    is_degraded,
    stub_artefact_ids,
)

# Committed fixtures, not `data/customer/` — that tree is gitignored run output,
# so tests bound to it fail on a fresh clone and change meaning after every run.
_DEGRADED = Path("tests/fixtures/degraded_run/eng-degraded_audit_state.json")
_CLEAN = Path("tests/fixtures/customer_finclear/eng-01_finclear_gmbh_audit_state.json")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ref(sha: str) -> dict:
    return {"uri": "minio://x/y.json", "sha256": sha, "template_id": "t"}


def test_stub_sha_is_the_only_marker() -> None:
    """A real artefact is not flagged by an empty or absent sha."""
    state = {"phase_artefacts": {"T02_system_card": _ref(""),
                                 "T03_annex_iii_mapping": {"uri": "u"},
                                 "T04_risk_tier_decision": _ref(STUB_SHA)}}
    assert stub_artefact_ids(state) == ["T04_risk_tier_decision"]


def test_degraded_phases_reports_the_owning_phase() -> None:
    """A stub degrades the phase that owns the template, not every emitter."""
    state = {"phase_artefacts": {"T11_robustness_report": _ref(STUB_SHA),
                                 "T14_governance_findings": _ref(STUB_SHA)}}
    assert degraded_phases(state) == ["P3", "P5"]


def test_namespaced_spawn_key_resolves_to_its_template() -> None:
    """``T11_robustness_report@Cyber`` degrades P3, not ``UNKNOWN``."""
    state = {"phase_artefacts": {"T11_robustness_report@Cyber": _ref(STUB_SHA)}}
    assert degraded_phases(state) == ["P3"]


def test_unknown_template_does_not_raise() -> None:
    """An artefact key outside the ownership map is reported, not dropped."""
    state = {"phase_artefacts": {"T99_invented": _ref(STUB_SHA)}}
    assert degraded_phases(state) == ["UNKNOWN"]


def test_empty_state_is_not_degraded() -> None:
    """No artefacts is not the same fact as placeholder artefacts."""
    assert not is_degraded({})
    assert build_run_integrity({})["suitable_for_handoff"]


def test_delivered_degraded_run_is_detected() -> None:
    """The 2026-09-03 delivery's shape is recognised as degraded."""
    block = build_run_integrity(_load(_DEGRADED))
    assert block["suitable_for_handoff"] is False
    assert block["degraded_phases"] == ["P1", "P5", "P6"]
    assert "T03_annex_iii_mapping" in block["stub_artefact_ids"]
    assert block["artefact_count"] == 19


def test_delivered_clean_run_is_suitable() -> None:
    """A run that reached every phase carries no placeholder.

    "Clean" has had to be backfilled into this fixture twice, each time behind a
    gate that grew a new way to be dirty. Fix F3 gave it a Phase 1 that actually
    ran. Then all sixteen of its critiques were found carrying
    ``llm_fallback_mode: True`` — every artefact rubber-stamped ``accept`` by the
    deterministic rubric, a *fully unverified* run standing as the suite's model
    of a healthy one — and were backfilled to model-authored on 2026-09-09.

    The third assertion is here so there is no fourth time: it states the
    property in the fixture rather than leaving it implied by the first.
    """
    block = build_run_integrity(_load(_CLEAN))
    assert block["suitable_for_handoff"] is True
    assert block["stub_artefact_ids"] == []
    assert block["degraded_phases"] == []
    assert block["fallback_critique_ids"] == []


def test_unwired_agents_default_to_what_the_run_recorded() -> None:
    """The writer need not thread the agent registry through to the block."""
    state = {"phase_artefacts": {}, "unwired_agents": ["scope_agent"]}
    assert build_run_integrity(state)["unwired_agents"] == ["scope_agent"]
    assert build_run_integrity(state, unwired_agents=[])["unwired_agents"] == []


def test_block_is_json_serialisable() -> None:
    """The block is written straight into a deliverable, so it must serialise."""
    block = build_run_integrity(_load(_DEGRADED))
    assert json.loads(json.dumps(block))["run_id"] == block["run_id"]
    assert RUN_INTEGRITY_KEY == "run_integrity"


def test_unwired_agent_reaches_the_handoff_warning() -> None:
    """The whole F4 chain: unwired agent → state → run_integrity → warning.

    This is the path that did not exist on 2026-09-03. The ScopeAgent was
    unwired, Phase 1 stubbed, and the only symptom that reached the consumer was
    an empty ``annex_iii_mapping`` two layers downstream.
    """
    from aaa.integrations.handoff import build_handoff

    state = {
        "engagement_id": "eng-test",
        "unwired_agents": ["scope_agent"],
        "final_verdict": "PASS",
        "phase_artefacts": {"T02_system_card": _ref(STUB_SHA)},
    }
    payload, warnings = build_handoff(state)
    assert payload["run_integrity"]["unwired_agents"] == ["scope_agent"]
    assert any("DEGRADED" in w for w in warnings)
    assert any("scope_agent" in w for w in warnings)
    assert any("final_verdict" in w for w in warnings)
