"""Part 1 of the former ``error_handler`` module (auto-split)."""
from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path

import structlog

_logger = structlog.get_logger("aaa.observability.error_handler")


LOG_DIR = Path("logs")


class ErrorLogHandler(logging.Handler):
    """Stdlib logging.Handler that writes ERROR and above to logs/errors/app.jsonl."""

    def __init__(self, component: str = "app") -> None:
        super().__init__(level=logging.ERROR)
        self._component = component
        self._path = LOG_DIR / "errors" / f"{component}.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        entry: dict[str, str | list[str]] = {
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
