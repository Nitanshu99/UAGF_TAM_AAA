"""
aaa.observability.logging_config — Structured JSON logging via structlog.

Call ``configure_logging()`` once at application startup (CLI entry point,
FastAPI lifespan, Dagster code location bootstrap). Every subsequent
``get_logger(__name__)`` returns a bound structlog logger that emits
newline-delimited JSON to stdout (and optionally a rotating file).

Log files are written to ``logs/<component>/`` so that each subsystem
(api, agents, llm_audit, errors) has its own rotated file.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path

import structlog


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_DIR = Path(os.environ.get("AAA_LOG_DIR", "logs"))
_CONFIGURED = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _file_handler(subdir: str, filename: str) -> logging.Handler:
    log_path = _ensure_dir(LOG_DIR / subdir) / filename
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def configure_logging(level: str | None = None) -> None:
    """Configure structlog + stdlib logging once.

    Safe to call multiple times — re-configuration is a no-op.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return

    from aaa.settings import settings  # lazy to avoid circular at import time

    log_level_str = level or settings.aaa_log_level
    log_level = getattr(logging, log_level_str.upper(), logging.WARNING)

    # ── stdlib root handler (JSON to stdout) ──────────────────────────────
    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(
        level=log_level,
        handlers=[
            root_handler,
            _file_handler("app", "app.log"),
        ],
    )

    # ── per-subsystem file handlers ───────────────────────────────────────
    for logger_name, subdir, filename in [
        ("aaa.api",           "api",       "api.log"),
        ("aaa.agents",        "agents",    "agents.log"),
        ("aaa.observability", "audit",     "llm_audit.log"),
        ("aaa.dagster",       "dagster",   "dagster.log"),
    ]:
        sub_logger = logging.getLogger(logger_name)
        sub_logger.addHandler(_file_handler(subdir, filename))

    # ── structlog processors ──────────────────────────────────────────────
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _CONFIGURED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger for *name*."""
    configure_logging()  # idempotent
    return structlog.get_logger(name)
