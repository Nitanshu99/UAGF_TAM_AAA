"""Prompt snapshot tests: the critique message envelope shape."""
from __future__ import annotations

import json

from aaa.agents.tier1.verifier import _SYSTEM_PROMPT, _build_critique_messages
from tests.unit.support.prompt_snapshots_data import (
    EMPTY_URIS_USER_SNAPSHOT,
    TWO_URIS_USER_SNAPSHOT,
)


def test_system_prompt_is_stable_across_calls():
    msgs_a = _build_critique_messages("P1", "T02", "{}", [])
    msgs_b = _build_critique_messages("P6", "T17", '{"x": 1}', ["ev://a"])
    assert msgs_a[0]["content"] == msgs_b[0]["content"]


def test_system_prompt_matches_module_constant():
    msgs = _build_critique_messages("P1", "T02", "{}", [])
    assert msgs[0]["content"] == _SYSTEM_PROMPT


def test_messages_list_has_two_entries():
    assert len(_build_critique_messages("P1", "T02", "{}", [])) == 2


def test_user_message_no_evidence_uris():
    msgs = _build_critique_messages(
        phase_id="P1", template_id="T02_system_card",
        content_str='{"hello": "world"}', evidence_uris=[])
    assert json.loads(msgs[1]["content"]) == EMPTY_URIS_USER_SNAPSHOT


def test_user_message_with_evidence_uris():
    msgs = _build_critique_messages(
        phase_id="P6", template_id="T17_compliance_matrix",
        content_str='{"in_scope_articles": ["Art.9", "Art.10"]}',
        evidence_uris=[
            "evidence://eng-001/p1/T02_system_card.json",
            "evidence://eng-001/p3/T11_robustness_report.json",
        ])
    assert json.loads(msgs[1]["content"]) == TWO_URIS_USER_SNAPSHOT


def test_user_message_contains_review_request_envelope():
    msgs = _build_critique_messages("P1", "T02", '{"sensitive": "data"}', [])
    user = json.loads(msgs[1]["content"])
    assert "review_request" in user
    assert user["review_request"]["artefact_payload"] == {"sensitive": "data"}


def test_user_message_includes_evidence_uri_list():
    msgs = _build_critique_messages("P1", "T02", "{}", ["ev://a"])
    assert json.loads(msgs[1]["content"])["review_request"]["evidence_uris"] == ["ev://a"]


def test_uri_order_is_preserved():
    msgs = _build_critique_messages(
        phase_id="P2", template_id="T06_datasheet_for_datasets", content_str="{}",
        evidence_uris=["evidence://b", "evidence://a", "evidence://c"])
    user = json.loads(msgs[1]["content"])
    assert user["review_request"]["evidence_uris"] == [
        "evidence://b", "evidence://a", "evidence://c"]
