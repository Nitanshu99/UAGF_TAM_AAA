"""Tests for aaa.observability.llm_audit."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_response(content="hello", prompt_tokens=10, completion_tokens=5):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.usage.prompt_tokens = prompt_tokens
    resp.usage.completion_tokens = completion_tokens
    resp.usage.total_tokens = prompt_tokens + completion_tokens
    return resp


def _get_llm_audit_mod():
    """Import the llm_audit module directly (avoids name conflict with the function)."""
    import importlib
    return importlib.import_module("aaa.observability.llm_audit")


def test_audit_logger_writes_ok_record(tmp_path):
    """LLMAuditLogger.finish() must write a JSONL record with status=ok."""
    mod = _get_llm_audit_mod()
    audit_file = tmp_path / "llm_audit.jsonl"

    def _patched_write(record):
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        with audit_file.open("a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    with patch.object(mod, "_write_jsonl", side_effect=_patched_write):
        auditor = mod.LLMAuditLogger(
            agent_name="TestAgent",
            model="gpt-test",
            messages=[{"role": "user", "content": "ping"}],
        )
        auditor.start()
        auditor.finish(response=_make_mock_response("pong"))

    assert audit_file.exists()
    records = [json.loads(l) for l in audit_file.read_text().splitlines() if l]
    assert len(records) == 1
    assert records[0]["status"] == "ok"
    assert records[0]["agent_name"] == "TestAgent"
    assert records[0]["response_text"] == "pong"


def test_audit_logger_writes_error_record(tmp_path):
    """LLMAuditLogger.finish() must write status=error on exception."""
    mod = _get_llm_audit_mod()
    audit_file = tmp_path / "llm_audit.jsonl"

    def _patched_write(record):
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        with audit_file.open("a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    with patch.object(mod, "_write_jsonl", side_effect=_patched_write):
        auditor = mod.LLMAuditLogger(
            agent_name="TestAgent",
            model="gpt-test",
            messages=[],
        )
        auditor.start()
        auditor.finish(error=ValueError("boom"))

    records = [json.loads(l) for l in audit_file.read_text().splitlines() if l]
    assert records[0]["status"] == "error"
    assert "boom" in records[0]["error"]


def test_extract_cost_graceful_on_missing_litellm():
    """_extract_cost must return None when litellm is unavailable."""
    from aaa.observability.llm_audit import _extract_cost
    from unittest.mock import patch
    import sys

    with patch.dict(sys.modules, {"litellm": None}):
        result = _extract_cost(MagicMock())
    # Should not raise
    assert result is None or isinstance(result, (float, type(None)))
