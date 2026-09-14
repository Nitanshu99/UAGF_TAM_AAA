"""Verifier review_request now threads artefact_uri + declaration_summary."""
from __future__ import annotations

import json

from aaa.agents.tier1.verifier import _build_critique_messages


def test_build_critique_messages_threads_artefact_uri_and_declaration():
    msgs = _build_critique_messages(
        "P1", "T02_system_card", '{"x": 1}', ["ev://a"],
        "minio://eng/phase_1/T02.json", {"declared_risk_tier": "high"},
    )
    req = json.loads(msgs[1]["content"])["review_request"]
    assert req["artefact_uri"] == "minio://eng/phase_1/T02.json"
    assert req["declaration_summary"] == {"declared_risk_tier": "high"}


def test_build_critique_messages_defaults_remain_empty_when_unset():
    # Backward compatibility: omitting the new args keeps the legacy empty shape.
    msgs = _build_critique_messages("P1", "T02", "{}", [])
    req = json.loads(msgs[1]["content"])["review_request"]
    assert req["artefact_uri"] == ""
    assert req["declaration_summary"] == {}
