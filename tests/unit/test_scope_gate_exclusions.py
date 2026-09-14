"""scope_gate: default in-scope path and Art. 5 / Art. 2 exclusions."""
from __future__ import annotations

import pytest

from aaa.tools.scope_gate import scope_gate
from tests.unit.support.scope_gate_fixture import base_payload


def test_empty_payload_defaults_to_in_scope():
    result = scope_gate({})
    assert result.verdict == "in_scope"
    assert result.halt_engagement is False
    assert result.reasoning  # non-empty


def test_legacy_fixture_is_in_scope():
    result = scope_gate(base_payload())
    assert result.verdict == "in_scope"
    assert result.become_provider_under_art25 is False
    assert result.triggers_fria is False
    assert result.is_gpai_systemic is False


def test_art5_prohibition_halts_engagement():
    result = scope_gate({**base_payload(),
                         "art5_prohibited_practices": ["social_scoring"]})
    assert result.verdict == "prohibited"
    assert result.halt_engagement is True
    assert "social_scoring" in result.reasoning[0]


def test_art5_none_value_does_not_trip_prohibition():
    result = scope_gate({**base_payload(), "art5_prohibited_practices": ["none"]})
    assert result.verdict == "in_scope"
    assert result.halt_engagement is False


@pytest.mark.parametrize("exclusion", ["military", "third_country_law_enforcement"])
def test_full_exclusions_route_to_excluded(exclusion: str):
    result = scope_gate({**base_payload(), "art2_exclusion": exclusion})
    assert result.verdict == "excluded"
    assert result.halt_engagement is True


@pytest.mark.parametrize(
    "exclusion", ["research_and_development", "open_source", "personal_use", "none"])
def test_partial_exclusions_do_not_halt(exclusion: str):
    result = scope_gate({**base_payload(), "art2_exclusion": exclusion})
    assert result.verdict == "in_scope"
    assert result.halt_engagement is False


def test_no_territorial_nexus_is_out_of_scope():
    result = scope_gate({**base_payload(), "territorial_scope": ["none"]})
    assert result.verdict == "out_of_scope"
    assert result.halt_engagement is True


def test_eu_market_nexus_is_in_scope():
    result = scope_gate({**base_payload(),
                        "territorial_scope": ["placed_on_eu_market"]})
    assert result.verdict == "in_scope"
