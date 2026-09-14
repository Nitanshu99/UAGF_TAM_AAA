"""The per-call LLM audit logger: one :class:`LLMAuditLogger` per LLM call."""
from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

from aaa.observability.llm_audit.build_record import build_record
from aaa.observability.llm_audit.record import _write_jsonl

_audit_logger = structlog.get_logger("aaa.observability.llm_audit")


class LLMAuditLogger:
    """Context manager that wraps one LLM call with full audit logging."""

    def __init__(self, agent_name: str, model: str, messages: list[dict[str, str]],
                 engagement_id: str | None = None, extra: dict[str, Any] | None = None) -> None:
        self.call_id = str(uuid.uuid4())
        self.agent_name = agent_name
        self.model = model
        self.messages = messages
        self.engagement_id = engagement_id
        self.extra = extra or {}
        self._start: float = 0.0

    def start(self) -> None:
        """Start the latency clock."""
        self._start = time.perf_counter()

    def finish(self, response: Any = None, error: BaseException | None = None) -> None:
        """Persist the record and emit the structlog event."""
        record = build_record(self, response=response, error=error)
        _write_jsonl(record)
        if error:
            _audit_logger.error(
                "llm_call_failed", **{k: v for k, v in record.items() if k != "messages"})
        else:
            _audit_logger.info(
                "llm_call_ok",
                **{k: v for k, v in record.items() if k not in ("messages", "response_text")})
