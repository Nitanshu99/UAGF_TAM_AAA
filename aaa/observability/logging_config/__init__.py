"""aaa.observability.logging_config — Structured JSON logging via structlog.

Call ``configure_logging()`` once at application startup (CLI entry point,
FastAPI lifespan). Every subsequent
``get_logger(__name__)`` returns a bound structlog logger that emits
newline-delimited JSON to stdout (and optionally a rotating file).

Log files are written to ``logs/<component>/`` so that each subsystem
(api, agents, llm_audit, errors) has its own rotated file."""
from aaa.observability.logging_config.configure_logging import configure_logging  # noqa: F401
from aaa.observability.logging_config.get_logger import get_logger  # noqa: F401
from aaa.observability.logging_config.log_dir import (  # noqa: F401
    _CONFIGURED,
    LOG_DIR,
    _ensure_dir,
    _file_handler,
)

__all__ = [
    'LOG_DIR',
    '_CONFIGURED',
    '_ensure_dir',
    '_file_handler',
    'configure_logging',
    'get_logger',
]
