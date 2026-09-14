"""scope_gate: derived flags (Art. 25 / 27 / 50 / 51) and render integration."""
from __future__ import annotations

from aaa.tools.scope_gate import ScopeGateResult, scope_gate
from aaa.tools.triage_render import triage_render
from tests.unit.support.scope_gate_fixture import base_payload


def test_art25_status_change_sets_provider_flag():
    result = scope_gate({**base_payload(),
                        "art25_status_change": ["substantial_modification"]})
    assert result.become_provider_under_art25 is True
    assert any("Art. 25" in r for r in result.reasoning)


def test_public_body_plus_high_risk_triggers_fria():
    result = scope_gate({**base_payload(), "is_public_body_or_public_service": True,
                        "declared_risk_tier": "high"})
    assert result.triggers_fria is True
    assert any("FRIA" in r for r in result.reasoning)


def test_public_body_with_limited_risk_no_fria():
    result = scope_gate({**base_payload(), "is_public_body_or_public_service": True,
                        "declared_risk_tier": "limited"})
    assert result.triggers_fria is False


def test_gpai_systemic_risk_flag():
    result = scope_gate({**base_payload(), "gpai_systemic_risk": True})
    assert result.is_gpai_systemic is True
    assert any("Art. 51" in r for r in result.reasoning)


def test_art50_triggers_set_flag():
    result = scope_gate({**base_payload(),
                        "art50_transparency_triggers": ["deepfake_content"]})
    assert result.triggers_art50_transparency is True


def test_triage_render_embeds_scope_gate_block():
    rendered = triage_render(base_payload())
    assert rendered.is_valid is True
    assert "scope_gate" in rendered.rendered
    block = rendered.rendered["scope_gate"]
    assert block["verdict"] == "in_scope"
    assert isinstance(block["reasoning"], list)


def test_to_dict_round_trips_all_fields():
    d = ScopeGateResult(verdict="in_scope").to_dict()
    for key in ("verdict", "reasoning", "become_provider_under_art25",
                "triggers_fria", "triggers_art50_transparency",
                "is_gpai_systemic", "halt_engagement"):
        assert key in d


def test_critical_infrastructure_is_excepted_from_fria():
    """Case 03: Art. 27(1) excepts Annex III point 2, public body or not."""
    result = scope_gate({**base_payload(), "is_public_body_or_public_service": True,
                        "declared_risk_tier": "high", "declared_annex_iii_sections": ["2"],
                        "entity_type": ["provider", "deployer"]})
    assert result.triggers_fria is False
    assert any("point 2" in r and "Art. 27(1)" in r for r in result.reasoning)


def test_a_public_deployer_in_another_area_still_owes_a_fria():
    """Point 2 alongside another area does not except the other use."""
    result = scope_gate({**base_payload(), "is_public_body_or_public_service": True,
                        "declared_risk_tier": "high", "declared_annex_iii_sections": ["2", "5"],
                        "entity_type": ["deployer"]})
    assert result.triggers_fria is True


def test_a_provider_that_does_not_deploy_owes_no_fria():
    """The Art. 27 duty is the deployer's."""
    result = scope_gate({**base_payload(), "is_public_body_or_public_service": True,
                        "declared_risk_tier": "high", "declared_annex_iii_sections": ["5"],
                        "entity_type": ["provider"]})
    assert result.triggers_fria is False
    assert any("not a deployer" in r for r in result.reasoning)
