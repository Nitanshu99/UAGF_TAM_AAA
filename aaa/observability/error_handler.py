"""
aaa.observability.error_handler — Centralised error capture and routing.

Every unhandled exception in an agent or API endpoint should pass through
``capture_error()`` (or its decorator equivalent).  The function:

1. Logs a structured JSON record via structlog to stderr / app.log.
2. Appends the error record to ``logs/errors/<component>.jsonl``
   so that each subsystem has its own error trail that can be
   independently shipped to an alerting system.
3. Optionally re-raises the exception (default: True).

Usage::

    from aaa.observability.error_handler import capture_error

    try:
        risky_operation()
    except Exception as exc:
        capture_error(exc, component="agents", context={"engagement_id": eid})
        raise
"""
from __future__ import annotations

import json
import logging
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

_logger = structlog.get_logger("aaa.observability.error_handler")

LOG_DIR = Path("logs")


# ---------------------------------------------------------------------------
# stdlib logging handler that routes ERROR+ to a dedicated file
# ---------------------------------------------------------------------------


class ErrorLogHandler(logging.Handler):
    """Stdlib logging.Handler that writes ERROR and above to logs/errors/app.jsonl."""

    def __init__(self, component: str = "app") -> None:
        super().__init__(level=logging.ERROR)
        self._component = component
        self._path = LOG_DIR / "errors" / f"{component}.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "component": self._component,
        }
        if record.exc_info:
            entry["traceback"] = traceback.format_exception(*record.exc_info)
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        except OSError:
            pass  # never let the error handler itself crash


# ---------------------------------------------------------------------------
# Functional capture helper
# ---------------------------------------------------------------------------


def capture_error(
    exc: BaseException,
    *,
    component: str = "app",
    context: dict[str, Any] | None = None,
    reraise: bool = True,
) -> None:
    """Log and persist an error record to ``logs/errors/<component>.jsonl``.

    Parameters
    ----------
    exc:
        The exception to record.
    component:
        Subsystem name — used as the JSONL filename stem.
        Suggested values: ``"api"``, ``"agents"``, ``"dagster"``,
        ``"observability"``.
    context:
        Extra key/value pairs to include in the record (engagement_id, etc.).
    reraise:
        When *True* (default) re-raises *exc* after logging.
    """
    error_id = str(uuid.uuid4())
    record: dict[str, Any] = {
        "error_id": error_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": traceback.format_exc(),
        **(context or {}),
    }

    _logger.error(
        "error_captured",
        error_id=error_id,
        component=component,
        exc_type=type(exc).__name__,
        **(context or {}),
    )

    out_path = LOG_DIR / "errors" / f"{component}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    except OSError:
        pass

    if reraise:
        raise exc
