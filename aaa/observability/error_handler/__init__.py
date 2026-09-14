"""aaa.observability.error_handler — Centralised error capture and routing.

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
        raise"""
from aaa.observability.error_handler.capture_error import capture_error  # noqa: F401
from aaa.observability.error_handler.logger import LOG_DIR, ErrorLogHandler, _logger  # noqa: F401

__all__ = [
    '_logger',
    'LOG_DIR',
    'ErrorLogHandler',
    'capture_error',
]
