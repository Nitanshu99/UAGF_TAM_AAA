"""Tests for aaa.observability.logging_config."""
from __future__ import annotations

import logging


def test_configure_logging_is_idempotent(tmp_path, monkeypatch):
    """configure_logging() must be callable multiple times without error."""
    monkeypatch.setenv("AAA_LOG_DIR", str(tmp_path / "logs"))
    # Reset the _CONFIGURED flag so we can test from scratch
    import aaa.observability.logging_config as lc
    lc._CONFIGURED = False

    lc.configure_logging("WARNING")
    lc.configure_logging("DEBUG")  # second call — must be a no-op

    assert lc._CONFIGURED is True


def test_get_logger_returns_bound_logger():
    """get_logger should return a structlog-wrapped logger."""
    import aaa.observability.logging_config as lc
    logger = lc.get_logger("test.module")
    assert logger is not None


def test_log_dir_created(tmp_path, monkeypatch):
    """configure_logging() must create log directories."""
    log_dir = tmp_path / "mylogdir"
    monkeypatch.setenv("AAA_LOG_DIR", str(log_dir))
    import aaa.observability.logging_config as lc
    lc._CONFIGURED = False
    lc.LOG_DIR = log_dir
    lc.configure_logging("WARNING")
    assert log_dir.exists()
