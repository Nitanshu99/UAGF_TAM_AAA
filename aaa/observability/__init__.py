"""aaa.observability — Structured logging, LLM audit, error routing, metrics."""

from aaa.observability.logging_config import configure_logging, get_logger
from aaa.observability.llm_audit import LLMAuditLogger, llm_audit
from aaa.observability.error_handler import capture_error, ErrorLogHandler
from aaa.observability.metrics import (
    LLM_CALL_COUNTER,
    LLM_LATENCY_HISTOGRAM,
    LLM_TOKEN_COUNTER,
    PHASE_LATENCY_HISTOGRAM,
    ERROR_COUNTER,
)

__all__ = [
    "configure_logging",
    "get_logger",
    "LLMAuditLogger",
    "llm_audit",
    "capture_error",
    "ErrorLogHandler",
    "LLM_CALL_COUNTER",
    "LLM_LATENCY_HISTOGRAM",
    "LLM_TOKEN_COUNTER",
    "PHASE_LATENCY_HISTOGRAM",
    "ERROR_COUNTER",
]
