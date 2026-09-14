"""Arts. 51-55 bind providers of a GPAI model, not consumers of one.

The generative modality alone used to select ``ARTICLE_SET["high_llm"]``, which
bundles the five GPAI obligations. On one engagement — a system that
consumes a hosted model and does not place a GPAI model on the market — all five were assessed and all five were PASSed, inflating regulatory
coverage from 42.9 % to 60.0 %.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.regulatory_coverage.article_set import (
    GPAI_PROVIDER_OBLIGATIONS,
    _resolve_article_set,
)


def _state(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"risk_tier": "high", "is_llm_or_agentic": True}
    base.update(over)
    return base


def test_consumer_of_a_gpai_model_does_not_carry_provider_obligations() -> None:
    """An explicit ``False`` removes Arts. 51-55 from scope."""
    got = _resolve_article_set(_state(gpai_general_purpose=False))
    assert not (got & GPAI_PROVIDER_OBLIGATIONS)
    assert "Art.9" in got and "Art.15" in got, "the high-risk duties must remain"


def test_declaration_is_read_from_the_nested_stage_a() -> None:
    """Stage A is stored nested and is not mirrored onto the audit state."""
    got = _resolve_article_set(_state(
        client_submission={"stage_a": {"gpai_general_purpose": False}}))
    assert not (got & GPAI_PROVIDER_OBLIGATIONS)


def test_an_actual_gpai_provider_still_carries_them() -> None:
    """Declaring the model is placed on the market keeps the obligations."""
    got = _resolve_article_set(_state(gpai_general_purpose=True))
    assert GPAI_PROVIDER_OBLIGATIONS <= got


def test_absent_declaration_is_conservative() -> None:
    """Unknown must not silently narrow the audit's scope."""
    assert GPAI_PROVIDER_OBLIGATIONS <= _resolve_article_set(_state())
