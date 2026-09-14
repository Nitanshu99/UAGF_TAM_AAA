"""Part 2 of the former ``logging_config`` module (auto-split)."""
from __future__ import annotations

import logging
import logging.handlers
import sys

import structlog

from aaa.observability.logging_config.formatter import json_formatter, shared_processors
from aaa.observability.logging_config.log_dir import (  # noqa: F401
    _CONFIGURED,
    LOG_DIR,
    _ensure_dir,
    _file_handler,
)

#: Loggers with their own rotating file, in addition to the root app.log.
_SUBSYSTEM_FILES = [
    ("aaa.api",           "api",       "api.log"),
    ("aaa.agents",        "agents",    "agents.log"),
    ("aaa.observability", "audit",     "llm_audit.log"),
]


def configure_logging(level: str | None = None) -> None:
    """Configure structlog + stdlib logging once.

    Safe to call multiple times — re-configuration is a no-op. Every handler
    renders JSON, for stdlib records as much as for structlog events, so the
    files Alloy tails are uniformly parseable (``level`` becomes a Loki label).
    """
    global _CONFIGURED  # noqa: PLW0603  # pylint: disable=global-statement
    if _CONFIGURED:
        return

    from aaa.settings import settings  # lazy to avoid circular at import time

    log_level_str = level or settings.aaa_log_level
    log_level = getattr(logging, log_level_str.upper(), logging.WARNING)
    formatter = json_formatter()

    # ── stdlib root handlers (JSON to stdout + app.log) ───────────────────
    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(formatter)
    logging.basicConfig(
        level=log_level,
        handlers=[root_handler, _file_handler("app", "app.log", formatter)],
    )

    # ── per-subsystem file handlers ───────────────────────────────────────
    for logger_name, subdir, filename in _SUBSYSTEM_FILES:
        logging.getLogger(logger_name).addHandler(_file_handler(subdir, filename, formatter))

    # ── structlog: shared chain, then hand off to the stdlib formatter ────
    structlog.configure(
        processors=[*shared_processors(), structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _CONFIGURED = True
