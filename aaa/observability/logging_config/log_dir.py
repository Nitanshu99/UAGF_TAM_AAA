"""Part 1 of the former ``logging_config`` module (auto-split)."""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(os.environ.get("AAA_LOG_DIR", "logs"))


_CONFIGURED = False


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _file_handler(subdir: str, filename: str,
                  formatter: logging.Formatter | None = None) -> logging.Handler:
    """Return a 10 MB × 5 rotating handler under ``LOG_DIR/subdir/filename``.

    :param formatter: Formatter to attach; defaults to the bare message.
    """
    log_path = _ensure_dir(LOG_DIR / subdir) / filename
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(formatter or logging.Formatter("%(message)s"))
    return handler
