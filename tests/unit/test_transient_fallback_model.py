"""One call whose retries are spent may fall back to a mapped free model — that call only.

User decision 2026-09-13: on the free route, a call exhausting its four retries on
nemotron-3-ultra:free is re-run on nemotron-3-super:free with its own four
retries; the run's model does not change, and the audit row names the model
that answered.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from aaa.agents.base import audit as audit_mod
from aaa.agents.base.agent import BaseAgent
from aaa.platform.phase_budget import bind_phase_deadline
from aaa.platform.transient_retry import (
    FALLBACK_MODELS,
    MAX_TRANSIENT_RETRIES,
    record_attempts,
    served_model_so_far,
    with_transient_retry,
)
from tests.unit.support.llm_audit_helpers import jsonl_writer, make_mock_response

ULTRA = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"
SUPER = "openrouter/nvidia/nemotron-3-super-120b-a12b:free"


class _ServiceUnavailableError(Exception):
    """``litellm.ServiceUnavailableError`` by type name."""


def _overloaded() -> _ServiceUnavailableError:
    return _ServiceUnavailableError("Upstream error from Nvidia: Service temporarily overloaded")


@pytest.fixture(autouse=True)
def _no_real_backoff(monkeypatch):
    from aaa.platform.transient_retry import latency

    latency.reset()
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    monkeypatch.delenv("AAA_TRANSIENT_FALLBACK", raising=False)


def _provider(fails_on: set[str], seen: list[str]):
    async def _call(**kwargs):
        seen.append(kwargs["model"])
        if kwargs["model"] in fails_on:
            raise _overloaded()
        return f"answered by {kwargs['model']}"
    return _call


def test_the_mapping_is_the_one_the_user_chose() -> None:
    assert FALLBACK_MODELS == {ULTRA: SUPER}


def test_an_exhausted_call_falls_back_for_that_call_only() -> None:
    seen: list[str] = []
    with record_attempts() as retried:
        reply = asyncio.run(with_transient_retry(_provider({ULTRA}, seen), model=ULTRA))
        assert served_model_so_far() == SUPER
    assert reply == f"answered by {SUPER}"
    assert seen == [ULTRA] * (MAX_TRANSIENT_RETRIES + 1) + [SUPER]
    assert len(retried) == MAX_TRANSIENT_RETRIES + 1


def test_the_fallback_gets_its_own_retries_and_then_fails_as_before() -> None:
    seen: list[str] = []
    with pytest.raises(_ServiceUnavailableError):
        asyncio.run(with_transient_retry(_provider({ULTRA, SUPER}, seen), model=ULTRA))
    assert seen.count(SUPER) == MAX_TRANSIENT_RETRIES + 1


def test_no_fallback_for_an_unmapped_model_a_non_transient_failure_or_when_disabled(monkeypatch) -> None:
    seen: list[str] = []
    with pytest.raises(_ServiceUnavailableError):
        asyncio.run(with_transient_retry(_provider({"openrouter/minimax/minimax-m3"}, seen),
                                         model="openrouter/minimax/minimax-m3"))
    assert SUPER not in seen

    async def _auth(**_kwargs):
        raise PermissionError("401 Invalid API key")
    with pytest.raises(PermissionError):
        asyncio.run(with_transient_retry(_auth, model=ULTRA))

    monkeypatch.setenv("AAA_TRANSIENT_FALLBACK", "off")
    seen.clear()
    with pytest.raises(_ServiceUnavailableError):
        asyncio.run(with_transient_retry(_provider({ULTRA}, seen), model=ULTRA))
    assert SUPER not in seen


def test_a_spent_phase_budget_does_not_fund_a_fallback() -> None:
    seen: list[str] = []
    with bind_phase_deadline(0.001):
        with pytest.raises(_ServiceUnavailableError):
            asyncio.run(with_transient_retry(_provider({ULTRA}, seen), model=ULTRA))
    assert SUPER not in seen


def test_the_audit_row_names_the_model_that_answered(tmp_path, monkeypatch) -> None:
    audit_file = tmp_path / "llm_audit.jsonl"
    monkeypatch.setattr(audit_mod, "_write_jsonl", jsonl_writer(audit_file))

    class _Agent(BaseAgent):
        async def process(self, message):
            return message

    async def _provider_call(**kwargs):
        if kwargs["model"] == ULTRA:
            raise _overloaded()
        return make_mock_response("pong")

    agent = _Agent("Verifier", ULTRA)
    with patch("aaa.platform.flex_retry.one_call.litellm", create=True):
        with patch("aaa.platform.flex_retry.flex_acompletion._acompletion_once",
                   side_effect=_provider_call):
            asyncio.run(agent.acompletion(messages=[{"role": "user", "content": "x"}]))
    record = json.loads(audit_file.read_text().splitlines()[0])
    assert record["model"] == ULTRA and record["served_model"] == SUPER
    assert record["status"] == "ok" and record["attempts"] == MAX_TRANSIENT_RETRIES + 2


def _tight_budget(monkeypatch, remaining: float, attempt_seconds: float) -> None:
    """A phase with *remaining* seconds left, whose attempts each take *attempt_seconds*."""
    from aaa.platform import phase_budget
    from aaa.platform.transient_retry import ladder as ladder_mod

    clock = iter(float(i) * attempt_seconds for i in range(10_000))
    monkeypatch.setattr(ladder_mod.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(ladder_mod, "backoff_seconds", lambda _retry, **_schedule: 1.0)
    monkeypatch.setattr(phase_budget, "remaining_seconds", lambda: remaining)


def test_the_last_funded_attempt_goes_to_the_fallback(monkeypatch) -> None:
    """Case 04, 2026-09-13: slow overload errors spent the budget and the fallback never ran.

    With room for one more attempt but not two, the primary does not take it.
    """
    _tight_budget(monkeypatch, remaining=3.0, attempt_seconds=1.5)
    seen: list[str] = []
    reply = asyncio.run(with_transient_retry(_provider({ULTRA}, seen), model=ULTRA))
    assert seen == [ULTRA, SUPER] and reply == f"answered by {SUPER}"


def test_a_model_without_a_fallback_keeps_the_attempt(monkeypatch) -> None:
    """Nothing to hand over to: the budget rule alone decides, as before."""
    _tight_budget(monkeypatch, remaining=3.0, attempt_seconds=1.5)
    seen: list[str] = []
    minimax = "openrouter/minimax/minimax-m3"
    with pytest.raises(_ServiceUnavailableError):
        asyncio.run(with_transient_retry(_provider({minimax}, seen), model=minimax))
    assert seen == [minimax] * (MAX_TRANSIENT_RETRIES + 1)


def test_a_lost_network_is_transient_but_a_bad_key_is_not() -> None:
    """Batch 3 (2026-09-13): DNS failed and every call ended at attempts=1."""
    from aaa.platform.transient_retry import is_transient

    class APIError(Exception):
        """``litellm.APIError`` by type name."""

    assert is_transient(APIError("OpenrouterException - Cannot connect to host openrouter.ai:443 "
                                 "ssl:<ssl.SSLContext> [nodename nor servname provided, or not known]"))
    assert not is_transient(APIError("AuthenticationError: 401 invalid api key"))


def test_a_measured_fast_fallback_gets_time_the_primary_cannot_use(monkeypatch) -> None:
    """T-082: a slow-failing primary no longer prices the fallback at its own failure latency."""
    from aaa.platform.transient_retry import latency

    _tight_budget(monkeypatch, remaining=3.0, attempt_seconds=4.0)
    latency.record_success(SUPER, 0.5)
    seen: list[str] = []
    reply = asyncio.run(with_transient_retry(_provider({ULTRA}, seen), model=ULTRA))
    assert seen == [ULTRA, SUPER] and reply == f"answered by {SUPER}"


def test_an_unmeasured_fallback_is_not_started_on_a_guess(monkeypatch) -> None:
    """With nothing measured, a primary attempt too slow to retry does not fund the fallback either."""
    _tight_budget(monkeypatch, remaining=3.0, attempt_seconds=4.0)
    seen: list[str] = []
    with pytest.raises(_ServiceUnavailableError):
        asyncio.run(with_transient_retry(_provider({ULTRA}, seen), model=ULTRA))
    assert seen == [ULTRA]


class Timeout(Exception):  # noqa: N818 — litellm.Timeout by type name
    """``litellm.Timeout`` by type name."""


def test_a_retry_that_hangs_to_its_reserving_ceiling_hands_over(monkeypatch) -> None:
    """T-085: a hung retry spent the fallback's reserved time and ended on a terminal timeout."""
    from aaa.platform import phase_budget
    from aaa.platform.transient_retry import latency

    monkeypatch.setattr(phase_budget, "remaining_seconds", lambda: 100.0)
    latency.record_success(SUPER, 5.0)
    seen: list[dict] = []

    async def provider(**kwargs):
        seen.append(kwargs)
        if kwargs["model"] == ULTRA:
            raise Timeout("litellm.Timeout: A Timeout Occurred")
        return "answered by super"

    assert asyncio.run(with_transient_retry(provider, model=ULTRA)) == "answered by super"
    assert seen[0]["_attempt_ceiling"] == 95.0 and "_attempt_ceiling" not in seen[1]


def test_a_timeout_without_a_fallback_is_still_terminal() -> None:
    """No fallback model: our own ceiling expiring is final, attempted once."""
    seen: list[str] = []

    async def provider(**kwargs):
        seen.append(kwargs["model"])
        raise Timeout("litellm.Timeout: A Timeout Occurred")

    with pytest.raises(Timeout):
        asyncio.run(with_transient_retry(provider, model="openrouter/minimax/minimax-m3"))
    assert seen == ["openrouter/minimax/minimax-m3"]


def test_the_client_ceiling_honours_the_attempt_cap(monkeypatch) -> None:
    """``flex_retry.one_call`` pops the cap and never lets LiteLLM see it."""
    import sys
    import types

    from aaa.platform.flex_retry.one_call import _acompletion_once

    sent: dict = {}

    async def acompletion(**kwargs):
        sent.update(kwargs)
        return "ok"

    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(acompletion=acompletion))
    monkeypatch.setattr("aaa.platform.rate_limit.acquire_for_model", AsyncMock())
    monkeypatch.setattr("aaa.observability.tracing.configure_llm_tracing", lambda: False)
    asyncio.run(_acompletion_once(model="openrouter/minimax/minimax-m3", messages=[],
                                  timeout=300, _attempt_ceiling=42.0))
    assert sent["timeout"] == 42.0 and "_attempt_ceiling" not in sent


def test_a_hung_call_outside_any_phase_hands_over(monkeypatch) -> None:
    """T-089: an unbound Orchestrator call hung to its ceiling and never reached super:free."""
    from aaa.platform import phase_budget

    monkeypatch.setattr(phase_budget, "remaining_seconds", lambda: None)
    seen: list[str] = []

    async def provider(**kwargs):
        seen.append(kwargs["model"])
        if kwargs["model"] == ULTRA:
            raise Timeout("litellm.Timeout: A Timeout Occurred")
        return "answered by super"

    assert asyncio.run(with_transient_retry(provider, model=ULTRA)) == "answered by super"
    assert seen == [ULTRA, SUPER]
