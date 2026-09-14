"""Fix 33 (Q9, Q10) — a cost column that says what it knows, and a line that arrives.

**Q9.** All 48 records of the part-2 run carried `estimated_cost_usd: 0.0000`.
Nothing was measured: `litellm.completion_cost` returns zero for a model absent
from its cost map, and every `nvidia_nim/*` identifier is absent from it. The run
happened to be on a free-tier account, so the number was right by accident; the
same code on a paid deployment reports the same 0.0000.

**Q10.** The preflight line exists to be read *before* the run spends anything,
and `print()` block-buffers when stdout is not a tty — so it reached the operator
at exit, 5,088 seconds after the decision it exists to inform.
"""
from __future__ import annotations

import io
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from aaa.observability.llm_audit.pricing import (
    DECLARED,
    LITELLM,
    UNPRICED,
    declared_prices,
    resolve_cost,
)

MODEL = "nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b"
USAGE = {"prompt_tokens": 9_459, "completion_tokens": 2_239}


@pytest.fixture(name="no_litellm")
def _no_litellm():
    """LiteLLM absent, or present with no rate for this model — the same answer."""
    with patch.dict(sys.modules, {"litellm": None}):
        yield


# ── Q9: zero and unknown are different statements ────────────────────────────

def test_a_model_nothing_can_price_is_recorded_unknown_not_free(no_litellm):
    """The whole of Q9: 0.0000 asserted the run was free."""
    cost, basis = resolve_cost(MagicMock(), MODEL, USAGE)

    assert cost is None
    assert basis == UNPRICED


def test_a_zero_from_litellm_is_read_as_no_rate(monkeypatch, no_litellm):
    """That zero is what "absent from the cost map" looks like, not a price."""
    cost, basis = resolve_cost(MagicMock(), MODEL, USAGE)

    assert (cost, basis) != (0.0, LITELLM)


def test_an_operator_declared_rate_prices_the_call(monkeypatch):
    monkeypatch.setenv("MODEL_PRICES_USD_PER_1M",
                       json.dumps({MODEL: {"input": 1.0, "output": 4.0}}))
    _reload_settings(monkeypatch)

    with patch.dict(sys.modules, {"litellm": None}):
        cost, basis = resolve_cost(MagicMock(), MODEL, USAGE)

    # 9459/1e6 * 1.0 + 2239/1e6 * 4.0
    assert cost == pytest.approx(0.018415, abs=1e-6)
    assert basis == DECLARED


def test_a_free_tier_operator_declares_zero_and_the_trail_says_so(monkeypatch):
    """Free is a claim someone makes, not a silence the reader has to interpret."""
    monkeypatch.setenv("MODEL_PRICES_USD_PER_1M",
                       json.dumps({MODEL: {"input": 0.0, "output": 0.0}}))
    _reload_settings(monkeypatch)

    with patch.dict(sys.modules, {"litellm": None}):
        cost, basis = resolve_cost(MagicMock(), MODEL, USAGE)

    assert (cost, basis) == (0.0, DECLARED)


def test_a_declared_rate_for_another_model_does_not_price_this_one(monkeypatch):
    monkeypatch.setenv("MODEL_PRICES_USD_PER_1M",
                       json.dumps({"openai/gpt-4": {"input": 1.0, "output": 1.0}}))
    _reload_settings(monkeypatch)

    with patch.dict(sys.modules, {"litellm": None}):
        cost, basis = resolve_cost(MagicMock(), MODEL, USAGE)

    assert (cost, basis) == (None, UNPRICED)


@pytest.mark.parametrize("raw", ["", "   ", "not json", "[1,2,3]"])
def test_an_unusable_price_declaration_is_ignored_loudly(monkeypatch, raw):
    monkeypatch.setenv("MODEL_PRICES_USD_PER_1M", raw)
    _reload_settings(monkeypatch)

    assert declared_prices() == {}


def test_the_audit_record_carries_the_basis_beside_the_number(monkeypatch, tmp_path):
    """A reader has to be able to tell a measured cost from a declared one."""
    from aaa.observability.llm_audit import record as record_mod

    monkeypatch.setattr(record_mod, "_AUDIT_JSONL", tmp_path / "audit.jsonl")
    from aaa.observability.llm_audit.call_logger import LLMAuditLogger

    auditor = LLMAuditLogger("Verifier", MODEL, [{"role": "user", "content": "x"}])
    auditor.start()
    with patch.dict(sys.modules, {"litellm": None}):
        auditor.finish(response=_response())

    written = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])
    assert written["estimated_cost_usd"] is None
    assert written["cost_basis"] == UNPRICED
    assert written["prompt_tokens"] == 9_459


def _response() -> MagicMock:
    response = MagicMock()
    response.usage.prompt_tokens = USAGE["prompt_tokens"]
    response.usage.completion_tokens = USAGE["completion_tokens"]
    response.usage.total_tokens = sum(USAGE.values())
    response.choices[0].message.content = "ok"
    return response


def _reload_settings(monkeypatch) -> None:
    """Rebuild the settings singleton so the patched env is read."""
    import aaa.settings as settings_mod
    from aaa.settings.model import AAASettings

    monkeypatch.setattr(settings_mod, "settings", AAASettings())


# ── Q10: the line that has to arrive before the spending starts ──────────────

def test_the_preflight_line_is_flushed_when_it_is_written():
    """Block-buffered, it reached the operator 5,088 seconds late."""
    from scripts.run_mock_case import evidence

    flushed: list[bool] = []

    class _Stream(io.StringIO):
        def flush(self) -> None:
            flushed.append(True)

    class _Store:
        is_durable = True

    stream = _Stream()
    with patch("sys.stdout", stream), \
            patch("aaa.platform.evidence.EvidenceStore", return_value=_Store()):
        rc = evidence.preflight_evidence_backend()

    assert rc == 0
    assert "evidence backend:" in stream.getvalue()
    assert flushed, "the preflight line must not wait for the process to exit"


def test_the_runner_line_buffers_its_whole_output():
    """`watch the per-phase progress logs below…` is an invitation the buffer refused."""
    from scripts.run_mock_case.env import unbuffer_output

    calls: list[dict] = []

    class _Reconfigurable:
        def reconfigure(self, **kwargs):
            calls.append(kwargs)

    with patch("sys.stdout", _Reconfigurable()), patch("sys.stderr", _Reconfigurable()):
        unbuffer_output()

    assert calls == [{"line_buffering": True}, {"line_buffering": True}]


def test_unbuffering_a_stream_that_cannot_be_reconfigured_is_a_no_op():
    """Under pytest's capture, stdout is not a reconfigurable TextIOWrapper."""
    from scripts.run_mock_case.env import unbuffer_output

    with patch("sys.stdout", io.StringIO()), patch("sys.stderr", object()):
        unbuffer_output()  # must not raise
