"""Part 3 of the former ``logging_config`` module (auto-split)."""
from __future__ import annotations

import structlog

from aaa.observability.logging_config.configure_logging import configure_logging  # noqa: F401
from aaa.observability.logging_config.log_dir import (  # noqa: F401
    _CONFIGURED,
    LOG_DIR,
    _ensure_dir,
    _file_handler,
)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger for *name*."""
    configure_logging()  # idempotent
    return structlog.get_logger(name)
