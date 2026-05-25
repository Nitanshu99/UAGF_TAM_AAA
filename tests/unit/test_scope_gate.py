"""
Unit tests for aaa.tools.scope_gate (FLI pre-intake scoping gate).

Covers:
  - Default in_scope verdict when FLI fields are absent (legacy fixtures)
  - Art. 5 prohibited practice halts the engagement
  - Art. 2 full exclusion (military / third-country LEA)
  - Out-of-scope when no territorial nexus is declared
  - Public-body + high-risk triggers FRIA flag
  - GPAI systemic-risk flag surfaced
  - Art. 25 status change sets become_provider_under_art25
  - Art. 50 triggers surfaced
  - Schema-validated payload integrates cleanly with triage_render
"""
from __future__ import annotations

import json
import pathlib

import pytest

from aaa.tools.scope_gate import scope_gate, ScopeGateResult
from aaa.tools.triage_render import triage_render

_FIXTURE = (
    pathlib.Path(__file__).parents[2]
    / "scripts" / "fixtures" / "uci_german_credit" / "stage_a.json"
)


def _base() -> dict:
    with _FIXTURE.open() as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Default / in-scope path
# ---------------------------------------------------------------------------

def test_empty_payload_defaults_to_in_scope():
    result = scope_gate({})
    assert result.verdict == "in_scope"
    assert result.halt_engagement is False
    assert result.reasoning  # non-empty


def test_legacy_fixture_is_in_scope():
    result = scope_gate(_base())
    assert result.verdict == "in_scope"
    assert result.become_provider_under_art25 is False
    assert result.triggers_fria is False
    assert result.is_gpai_systemic is False


# ---------------------------------------------------------------------------
# Art. 5 prohibitions
# ---------------------------------------------------------------------------

def test_art5_prohibition_halts_engagement():
    payload = {**_base(), "art5_prohibited_practices": ["social_scoring"]}
    result = scope_gate(payload)
    assert result.verdict == "prohibited"
    assert result.halt_engagement is True
    assert "social_scoring" in result.reasoning[0]


def test_art5_none_value_does_not_trip_prohibition():
    payload = {**_base(), "art5_prohibited_practices": ["none"]}
    result = scope_gate(payload)
    assert result.verdict == "in_scope"
    assert result.halt_engagement is False


# ---------------------------------------------------------------------------
# Art. 2 exclusions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "exclusion", ["military", "third_country_law_enforcement"]
)
def test_full_exclusions_route_to_excluded(exclusion: str):
    payload = {**_base(), "art2_exclusion": exclusion}
    result = scope_gate(payload)
    assert result.verdict == "excluded"
    assert result.halt_engagement is True


@pytest.mark.parametrize(
    "exclusion", ["research_and_development", "open_source", "personal_use", "none"]
)
def test_partial_exclusions_do_not_halt(exclusion: str):
    payload = {**_base(), "art2_exclusion": exclusion}
    result = scope_gate(payload)
    assert result.verdict == "in_scope"
    assert result.halt_engagement is False


# ---------------------------------------------------------------------------
# Art. 2 territorial scope
# ---------------------------------------------------------------------------

def test_no_territorial_nexus_is_out_of_scope():
    payload = {**_base(), "territorial_scope": ["none"]}
    result = scope_gate(payload)
    assert result.verdict == "out_of_scope"
    assert result.halt_engagement is True


def test_eu_market_nexus_is_in_scope():
    payload = {**_base(), "territorial_scope": ["placed_on_eu_market"]}
    result = scope_gate(payload)
    assert result.verdict == "in_scope"


# ---------------------------------------------------------------------------
# Derived flags (Art. 25 / Art. 27 / Art. 50 / Art. 51)
# ---------------------------------------------------------------------------

def test_art25_status_change_sets_provider_flag():
    payload = {**_base(), "art25_status_change": ["substantial_modification"]}
    result = scope_gate(payload)
    assert result.become_provider_under_art25 is True
    assert any("Art. 25" in r for r in result.reasoning)


def test_public_body_plus_high_risk_triggers_fria():
    payload = {**_base(), "is_public_body_or_public_service": True,
               "declared_risk_tier": "high"}
    result = scope_gate(payload)
    assert result.triggers_fria is True
    assert any("FRIA" in r for r in result.reasoning)


def test_public_body_with_limited_risk_no_fria():
    payload = {**_base(), "is_public_body_or_public_service": True,
               "declared_risk_tier": "limited"}
    result = scope_gate(payload)
    assert result.triggers_fria is False


def test_gpai_systemic_risk_flag():
    payload = {**_base(), "gpai_systemic_risk": True}
    result = scope_gate(payload)
    assert result.is_gpai_systemic is True
    assert any("Art. 51" in r for r in result.reasoning)


def test_art50_triggers_set_flag():
    payload = {**_base(), "art50_transparency_triggers": ["deepfake_content"]}
    result = scope_gate(payload)
    assert result.triggers_art50_transparency is True


# ---------------------------------------------------------------------------
# Integration: schema validation + scope_gate annotation in rendered output
# ---------------------------------------------------------------------------

def test_triage_render_embeds_scope_gate_block():
    rendered = triage_render(_base())
    assert rendered.is_valid is True
    assert "scope_gate" in rendered.rendered
    block = rendered.rendered["scope_gate"]
    assert block["verdict"] == "in_scope"
    assert isinstance(block["reasoning"], list)


def test_to_dict_round_trips_all_fields():
    result = ScopeGateResult(verdict="in_scope")
    d = result.to_dict()
    for key in (
        "verdict", "reasoning", "become_provider_under_art25",
        "triggers_fria", "triggers_art50_transparency",
        "is_gpai_systemic", "halt_engagement",
    ):
        assert key in d
