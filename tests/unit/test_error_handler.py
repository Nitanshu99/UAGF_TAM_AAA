"""Tests for aaa.observability.error_handler."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


def test_capture_error_writes_jsonl(tmp_path):
    """capture_error must write a JSONL record to logs/errors/<component>.jsonl."""
    import aaa.observability.error_handler as eh

    orig_log_dir = eh.LOG_DIR
    eh.LOG_DIR = tmp_path

    exc = ValueError("test error")
    with pytest.raises(ValueError, match="test error"):
        eh.capture_error(exc, component="test_comp", context={"foo": "bar"})

    eh.LOG_DIR = orig_log_dir

    out_path = tmp_path / "errors" / "test_comp.jsonl"
    assert out_path.exists()
    records = [json.loads(l) for l in out_path.read_text().splitlines() if l]
    assert len(records) == 1
    record = records[0]
    assert record["exception_type"] == "ValueError"
    assert record["exception_message"] == "test error"
    assert record["foo"] == "bar"
    assert record["component"] == "test_comp"
    assert "error_id" in record
    assert "traceback" in record


def test_capture_error_no_reraise(tmp_path):
    """capture_error with reraise=False must not raise."""
    import aaa.observability.error_handler as eh

    orig = eh.LOG_DIR
    eh.LOG_DIR = tmp_path
    eh.capture_error(RuntimeError("silent"), component="app", reraise=False)
    eh.LOG_DIR = orig
    # Should not raise


def test_error_log_handler_writes(tmp_path):
    """ErrorLogHandler must write ERROR+ log records to a dedicated file."""
    import logging
    import aaa.observability.error_handler as eh

    orig = eh.LOG_DIR
    eh.LOG_DIR = tmp_path

    handler = eh.ErrorLogHandler(component="app_test")
    logger = logging.getLogger("test_error_handler_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.error("Something went wrong")

    eh.LOG_DIR = orig

    out_path = tmp_path / "errors" / "app_test.jsonl"
    assert out_path.exists()
    records = [json.loads(l) for l in out_path.read_text().splitlines() if l]
    assert any("Something went wrong" in r.get("message", "") for r in records)
