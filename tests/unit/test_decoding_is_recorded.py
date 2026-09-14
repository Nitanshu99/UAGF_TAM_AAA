"""What was asked for and what was sent are both on the record, and they can differ.

OpenAI's reasoning models accept no temperature, so on the default roster only
``seed`` goes out and greedy decoding is not in effect. These tests hold the record
honest about that, on both audit writers (T-20260913-003); the run-level stamp is
``test_decoding_provenance``.

They run LiteLLM's real provider resolution and parameter mapping, and they must
pass on both LiteLLM 1.86.0 (the pin) and 1.100.1: the two disagree on whether
``gpt-5.6-*`` may be sent a temperature, which is exactly what went wrong once.
"""
from __future__ import annotations

from typing import Any

import pytest

from aaa.platform.model_registry.decoding import DEFAULT_SEED, sent_decoding

GREEDY = {"temperature": 0.0, "seed": DEFAULT_SEED}


@pytest.mark.parametrize("model", ["openrouter/minimax/minimax-m3",
                                   "nvidia_nim/nvidia/nemotron-3-ultra-550b-a55b"])
def test_greedy_reaches_the_open_weight_routes(model: str) -> None:
    """The routes the real runs used send both parameters."""
    assert sent_decoding(model) == GREEDY


@pytest.mark.parametrize("model", ["gpt-5.6-terra", "gpt-5"])
def test_a_reasoning_model_is_sent_the_seed_only(model: str) -> None:
    """Asked for temperature 0, sent none: the record must say so."""
    assert sent_decoding(model) == {"seed": DEFAULT_SEED}


def test_an_unmappable_model_is_unknown_not_empty() -> None:
    """``{}`` would claim nothing was sent; ``None`` says LiteLLM could not tell."""
    assert sent_decoding("no-such-provider/and-no-model") is None


def test_the_audit_row_records_both_halves(monkeypatch: pytest.MonkeyPatch) -> None:
    """Request and wire both on the row, for a model that cannot be greedy."""
    import aaa.agents.base.audit as mod

    written: list[dict[str, Any]] = []
    monkeypatch.setattr(mod, "_write_jsonl", written.append)
    mod.write_audit("Verifier", "gpt-5.6-terra", [], "call-1", 0.0, error=RuntimeError("x"))

    assert written, "the call was not audited at all"
    seed_only = {"seed": DEFAULT_SEED}
    assert written[0]["decoding"] == {"requested": seed_only, "sent": seed_only}


def test_the_other_audit_writer_has_the_same_shape() -> None:
    """Two writers once drifted apart on ``attempts``; they must not on this."""
    from aaa.observability.llm_audit.build_record import build_record
    from aaa.observability.llm_audit.call_logger import LLMAuditLogger

    call = LLMAuditLogger(agent_name="Verifier", model="openrouter/minimax/minimax-m3",
                          messages=[])
    call.start()
    record = build_record(call, error=RuntimeError("x"))
    assert record["decoding"] == {"requested": GREEDY, "sent": GREEDY}


def test_the_row_is_still_written_when_litellm_cannot_be_imported(tmp_path) -> None:
    """The record degrades to "unknown"; the audit trail never breaks for it."""
    import json
    import sys
    from unittest.mock import patch

    from aaa.observability.llm_audit import record as record_mod
    from aaa.observability.llm_audit.call_logger import LLMAuditLogger

    call = LLMAuditLogger("Verifier", "openrouter/vendor/only-in-this-test", [])
    call.start()
    with patch.object(record_mod, "_AUDIT_JSONL", tmp_path / "audit.jsonl"), \
            patch.dict(sys.modules, {"litellm": None, "litellm.utils": None}):
        call.finish(error=RuntimeError("x"))
    row = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])
    assert row["decoding"] == {"requested": GREEDY, "sent": None}
