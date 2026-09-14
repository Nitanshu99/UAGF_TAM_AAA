"""An unreadable critique is re-asked before the deterministic fallback.

On 2026-09-11 a T03 critique came back truncated — 81 completion tokens, cut off
inside ``"issues":[{"`` — so the JSON never closed. Lenient parsing cannot
rescue that, the critique was filed as ``unverified`` on the first attempt, and
Art. 6 and Annex III were recorded INSUFFICIENT_EVIDENCE for want of a verdict.

That is the same pair of articles the lenient parser was introduced to protect
after the 2026-09-10 GLM run discarded 6 of 17 critiques. Truncation is
transient; one retry is the difference between a judged artefact and an
unjudged one.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aaa.agents.tier1.verifier.llm import _critique_once

GOOD = ('{"message_type":"Critique","verdict":"ACCEPT_WITH_OBSERVATIONS",'
        '"scores":{"factual_accuracy":3},"issues":[]}')
#: The shape the provider actually returned: valid prefix, never closed.
TRUNCATED = ('{"message_type":"Critique","phase_id":"P1","scores":'
             '{"factual_accuracy":3,"completeness":2},"verdict":'
             '"ACCEPT_WITH_OBSERVATIONS","issues":[{"')


class _Agent:
    """Verifier stub returning a scripted reply per call."""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls = 0

    async def acompletion(self, **_kwargs: Any) -> Any:
        """Return the next scripted reply."""
        self.calls += 1
        text = self.replies.pop(0)
        return type("R", (), {"choices": [type("C", (), {
            "message": type("M", (), {"content": text})()})()]})()


def _run(agent: _Agent) -> dict:
    """Drive ``_critique_once`` synchronously."""
    return asyncio.run(_critique_once(agent, [], "P1", "T03_annex_iii_mapping"))


def test_a_truncated_reply_is_re_asked_and_the_retry_is_used() -> None:
    """The exact regression: one bad reply must not cost an artefact its verdict."""
    agent = _Agent([TRUNCATED, GOOD])
    result = _run(agent)
    assert agent.calls == 2
    assert result["verdict"] == "ACCEPT_WITH_OBSERVATIONS"


def test_a_readable_reply_is_not_re_asked() -> None:
    """No extra spend when the first answer is fine."""
    agent = _Agent([GOOD])
    assert _run(agent)["verdict"] == "ACCEPT_WITH_OBSERVATIONS"
    assert agent.calls == 1


def test_two_unreadable_replies_surface_rather_than_hang() -> None:
    """The caller still gets its deterministic fallback, after a real attempt."""
    agent = _Agent([TRUNCATED, TRUNCATED])
    with pytest.raises(ValueError, match="unreadable after 2 attempts"):
        _run(agent)
    assert agent.calls == 2


def test_a_reply_with_no_verdict_is_re_asked() -> None:
    """A fragment that parses but judges nothing is not a critique."""
    agent = _Agent(['{"scores":{"factual_accuracy":3}}', GOOD])
    assert _run(agent)["verdict"] == "ACCEPT_WITH_OBSERVATIONS"
    assert agent.calls == 2


def test_a_fenced_reply_still_parses_without_a_retry() -> None:
    """The 2026-09-10 fix stays: leniency handles fences on the first attempt."""
    agent = _Agent([f"```json\n{GOOD}\n```"])
    assert _run(agent)["verdict"] == "ACCEPT_WITH_OBSERVATIONS"
    assert agent.calls == 1
