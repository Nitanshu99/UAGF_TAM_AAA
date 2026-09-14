"""A declared Annex I Section A product reaches Art. 43 §3 through every door.

Every reader used ``annex_i_section_a_acts``; the Stage A contract calls the field
``annex_i_section_a``. State always carried an empty list, so a declared safety
component could never take the sectoral procedure (T-20260913-016).
"""
from __future__ import annotations

import json
from pathlib import Path

from aaa.agents.intake_validator.stage.a import preview_art43
from aaa.agents.tier1.phases.initial_state.build_initial_state import build_initial_state
from aaa.agents.tier2.scope_agent.diffing import decide_art43
from aaa.tools.art43_select.annex_i import ANNEX_I_SECTION_A

CONTRACT = json.loads(Path("templates/T01a_stage_a_triage.json").read_text(encoding="utf-8"))
STAGE_A = {"declared_risk_tier": "high", "declared_annex_iii_sections": [],
           "declared_modality": "cv", "annex_i_section_a": ["machinery"]}


def test_the_catalogue_is_keyed_by_the_contracts_own_ids() -> None:
    """Every act the form can declare has its citation, and no other id exists."""
    enum = CONTRACT["properties"]["annex_i_section_a"]["items"]["enum"]
    assert set(ANNEX_I_SECTION_A) == set(enum)


def test_the_intake_preview_takes_the_sectoral_procedure() -> None:
    """Stage A's own preview sees the declared machinery act."""
    decision = preview_art43(STAGE_A)
    assert decision["procedure"] == "annex_i_sectoral"
    assert "Directive 2006/42/EC" in decision["rationale"]


def test_initial_state_carries_the_declared_acts() -> None:
    """The CLI and API entry builds state from the contract key."""
    state = build_initial_state("eng-t", {"stage_a": STAGE_A, "stage_b": {}})
    assert state["annex_i_section_a_acts"] == ["machinery"]


def test_phase_1_decides_from_t01a_and_the_dispatch() -> None:
    """Phase 1 reads the acts from T01a and harmonised standards from state, via the dispatch."""
    art43, _preview, _delta, pseudo = decide_art43(
        STAGE_A, "high", [], {"harmonised_standards_applied": True})
    assert art43["procedure"] == "annex_i_sectoral"
    assert pseudo["harmonised_standards_applied"] is True
