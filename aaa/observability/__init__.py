"""aaa.observability — Structured logging, LLM audit, error routing, metrics."""

from aaa.observability.error_handler import ErrorLogHandler, capture_error
from aaa.observability.llm_audit import LLMAuditLogger, llm_audit
from aaa.observability.logging_config import configure_logging, get_logger
from aaa.observability.metrics import (
    ERROR_COUNTER,
    LLM_CALL_COUNTER,
    LLM_LATENCY_HISTOGRAM,
    LLM_TOKEN_COUNTER,
    PHASE_LATENCY_HISTOGRAM,
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
