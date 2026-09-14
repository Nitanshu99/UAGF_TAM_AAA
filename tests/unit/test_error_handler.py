"""Tests for aaa.observability.error_handler."""
from __future__ import annotations

import importlib
import json

import pytest

_CAPTURE_MOD = importlib.import_module("aaa.observability.error_handler.capture_error")
_LOGGER_MOD = importlib.import_module("aaa.observability.error_handler.logger")


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    """Redirect the error-handler log directory to a temp path."""
    monkeypatch.setattr(_CAPTURE_MOD, "LOG_DIR", tmp_path)
    monkeypatch.setattr(_LOGGER_MOD, "LOG_DIR", tmp_path)
    return tmp_path


def test_capture_error_writes_jsonl(log_dir):
    """capture_error must write a JSONL record to logs/errors/<component>.jsonl."""
    from aaa.observability.metrics import ERROR_COUNTER
    before = ERROR_COUNTER.labels(component="test_comp", exception_type="ValueError")._value.get()

    exc = ValueError("test error")
    with pytest.raises(ValueError, match="test error"):
        _CAPTURE_MOD.capture_error(exc, component="test_comp", context={"foo": "bar"})

    after = ERROR_COUNTER.labels(component="test_comp", exception_type="ValueError")._value.get()
    assert after == before + 1

    out_path = log_dir / "errors" / "test_comp.jsonl"
    assert out_path.exists()
    records = [json.loads(line) for line in out_path.read_text().splitlines() if line]
    assert len(records) == 1
    record = records[0]
    assert record["exception_type"] == "ValueError"
    assert record["exception_message"] == "test error"
    assert record["foo"] == "bar"
    assert record["component"] == "test_comp"
    assert "error_id" in record
    assert "traceback" in record


def test_capture_error_no_reraise(log_dir):
    """capture_error with reraise=False must not raise."""
    _CAPTURE_MOD.capture_error(RuntimeError("silent"), component="app", reraise=False)


def test_error_log_handler_writes(log_dir):
    """ErrorLogHandler must write ERROR+ log records to a dedicated file."""
    import logging

    handler = _LOGGER_MOD.ErrorLogHandler(component="app_test")
    logger = logging.getLogger("test_error_handler_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.error("Something went wrong")
    logger.removeHandler(handler)

    out_path = log_dir / "errors" / "app_test.jsonl"
    assert out_path.exists()
    records = [json.loads(line) for line in out_path.read_text().splitlines() if line]
    assert any("Something went wrong" in r.get("message", "") for r in records)
