"""Fix 39 — the audit trail says whether a reply took one attempt or two.

A retry that leaves no trace makes the trail *less* honest than before: every
row would read ``status: "ok"`` and the reader could no longer tell a provider
that answered from one that had to be asked twice. These tests pin the
distinction end to end, through ``BaseAgent.acompletion``.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from aaa.agents.base import audit as audit_mod
from aaa.agents.base.agent import BaseAgent
from aaa.platform.transient_retry import MAX_TRANSIENT_RETRIES
from tests.unit.support.llm_audit_helpers import jsonl_writer, make_mock_response


class _ServiceUnavailableError(Exception):
    """``litellm.ServiceUnavailableError`` by type name."""


def _overloaded() -> _ServiceUnavailableError:
    return _ServiceUnavailableError("ServiceUnavailableError: Nvidia_nimException - "
                       "Service temporarily overloaded")


class _Agent(BaseAgent):
    """Smallest concrete BaseAgent — the plumbing is what is under test."""

    async def process(self, message):
        return message


@pytest.fixture(name="records")
def _records(tmp_path, monkeypatch):
    """Redirect the audit JSONL and hand back a reader for it."""
    audit_file = tmp_path / "llm_audit.jsonl"
    monkeypatch.setattr(audit_mod, "_write_jsonl", jsonl_writer(audit_file))
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    return lambda: [json.loads(line)
                    for line in audit_file.read_text().splitlines() if line]


def _run(agent, provider):
    """Drive one ``acompletion`` with *provider* standing in for litellm."""
    with patch("aaa.platform.flex_retry.one_call.litellm", create=True):
        with patch("aaa.platform.flex_retry.flex_acompletion._acompletion_once",
                   side_effect=provider):
            return asyncio.run(agent.acompletion(messages=[{"role": "user", "content": "x"}]))


def test_a_first_attempt_success_records_one_attempt(records):
    agent = _Agent("TestAgent", "nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b")

    async def _ok(**_kwargs):
        return make_mock_response("pong")

    _run(agent, _ok)
    record = records()[0]
    assert record["status"] == "ok"
    assert record["attempts"] == 1
    assert "retried_after" not in record


def test_a_recovered_call_records_two_attempts_and_what_it_survived(records):
    """Case 01 #026 and case 04 #018 are exactly this shape."""
    agent = _Agent("Verifier", "nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b")
    state = {"n": 0}

    async def _fails_once(**_kwargs):
        state["n"] += 1
        if state["n"] == 1:
            raise _overloaded()
        return make_mock_response("pong")

    _run(agent, _fails_once)
    record = records()[0]
    assert record["status"] == "ok"
    assert record["attempts"] == 2
    assert "Service temporarily overloaded" in record["retried_after"][0]


def test_an_exhausted_retry_is_still_an_error_record_with_nothing_fabricated(records):
    agent = _Agent("Verifier", "nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b")

    async def _always_fails(**_kwargs):
        raise _overloaded()

    with pytest.raises(_ServiceUnavailableError):
        _run(agent, _always_fails)
    record = records()[0]
    assert record["status"] == "error"
    assert record["attempts"] == MAX_TRANSIENT_RETRIES + 1
    assert "response_text" not in record
