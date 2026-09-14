"""LLMAuditLogger JSONL record writing (ok and error paths)."""
from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

from tests.unit.support.llm_audit_helpers import jsonl_writer, llm_audit_mod, make_mock_response


def test_audit_logger_writes_ok_record(tmp_path):
    """LLMAuditLogger.finish() must write a JSONL record with status=ok."""
    mod = llm_audit_mod()
    audit_file = tmp_path / "llm_audit.jsonl"
    with patch.object(mod, "_write_jsonl", side_effect=jsonl_writer(audit_file)):
        auditor = mod.LLMAuditLogger(agent_name="TestAgent", model="gpt-test",
                                     messages=[{"role": "user", "content": "ping"}])
        auditor.start()
        auditor.finish(response=make_mock_response("pong"))
    records = [json.loads(line) for line in audit_file.read_text().splitlines() if line]
    assert len(records) == 1
    assert records[0]["status"] == "ok"
    assert records[0]["agent_name"] == "TestAgent"
    assert records[0]["response_text"] == "pong"


def test_audit_logger_writes_error_record(tmp_path):
    """LLMAuditLogger.finish() must write status=error on exception."""
    mod = llm_audit_mod()
    audit_file = tmp_path / "llm_audit.jsonl"
    with patch.object(mod, "_write_jsonl", side_effect=jsonl_writer(audit_file)):
        auditor = mod.LLMAuditLogger(agent_name="TestAgent", model="gpt-test",
                                     messages=[])
        auditor.start()
        auditor.finish(error=ValueError("boom"))
    records = [json.loads(line) for line in audit_file.read_text().splitlines() if line]
    assert records[0]["status"] == "error"
    assert "boom" in records[0]["error"]


def test_pricing_graceful_on_missing_litellm():
    """An unpriceable call is recorded as unknown, never as 0.0 (Q9)."""
    from aaa.observability.llm_audit.pricing import UNPRICED, resolve_cost
    with patch.dict(sys.modules, {"litellm": None}):
        cost, basis = resolve_cost(MagicMock(), "nvidia_nim/some/model", {})
    assert cost is None and basis == UNPRICED
