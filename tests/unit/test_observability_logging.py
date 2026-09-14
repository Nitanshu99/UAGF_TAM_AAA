"""Tests for aaa.observability.logging_config."""
from __future__ import annotations

import importlib
import json
import logging

_CONFIGURE_MOD = importlib.import_module("aaa.observability.logging_config.configure_logging")
_LOG_DIR_MOD = importlib.import_module("aaa.observability.logging_config.log_dir")


def test_configure_logging_is_idempotent(tmp_path, monkeypatch):
    """configure_logging() must be callable multiple times without error."""
    monkeypatch.setenv("AAA_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(_LOG_DIR_MOD, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(_CONFIGURE_MOD, "_CONFIGURED", False)

    _CONFIGURE_MOD.configure_logging("WARNING")
    _CONFIGURE_MOD.configure_logging("DEBUG")  # second call — must be a no-op

    assert _CONFIGURE_MOD._CONFIGURED is True


def test_get_logger_returns_bound_logger():
    """get_logger should return a structlog-wrapped logger."""
    import aaa.observability.logging_config as lc
    logger = lc.get_logger("test.module")
    assert logger is not None


def test_log_dir_created(tmp_path, monkeypatch):
    """configure_logging() must create log directories."""
    log_dir = tmp_path / "mylogdir"
    monkeypatch.setenv("AAA_LOG_DIR", str(log_dir))
    monkeypatch.setattr(_LOG_DIR_MOD, "LOG_DIR", log_dir)
    monkeypatch.setattr(_CONFIGURE_MOD, "_CONFIGURED", False)
    _CONFIGURE_MOD.configure_logging("WARNING")
    assert log_dir.exists()


def test_stdlib_records_are_rendered_as_json(tmp_path, monkeypatch):
    """A plain logging.getLogger() call lands in its file as one JSON object.

    agents.log used to hold text lines only, so Alloy could not extract a
    ``level`` label; the ProcessorFormatter gives stdlib records the same
    ``event``/``level``/``logger``/``timestamp`` shape as structlog events.
    """
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("AAA_LOG_DIR", str(log_dir))
    monkeypatch.setattr(_LOG_DIR_MOD, "LOG_DIR", log_dir)
    monkeypatch.setattr(_CONFIGURE_MOD, "_CONFIGURED", False)
    _CONFIGURE_MOD.configure_logging("INFO")

    probe = logging.getLogger("aaa.agents.test_json_probe")
    probe.warning("plain %s from stdlib", "text")
    for handler in logging.getLogger("aaa.agents").handlers:
        handler.flush()

    lines = (log_dir / "agents" / "agents.log").read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[-1])
    assert record["event"] == "plain text from stdlib"
    assert record["level"] == "warning"
    assert record["logger"] == "aaa.agents.test_json_probe"
    assert "timestamp" in record
