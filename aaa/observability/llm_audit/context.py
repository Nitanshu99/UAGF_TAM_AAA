"""Async context manager wrapping a single LLM call with audit logging."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from aaa.observability.llm_audit.call_logger import LLMAuditLogger


@asynccontextmanager
async def llm_audit(agent_name: str, model: str, messages: list[dict[str, str]],
                    engagement_id: str | None = None,
                    extra: dict[str, Any] | None = None) -> AsyncIterator[LLMAuditLogger]:
    """Async context manager wrapping a single LLM call with audit logging."""
    auditor = LLMAuditLogger(agent_name=agent_name, model=model, messages=messages,
                             engagement_id=engagement_id, extra=extra)
    auditor.start()
    response = None
    try:
        yield auditor
    except Exception as exc:
        auditor.finish(error=exc)
        raise
    # Reached only on success — the except handler always re-raises.
    auditor.finish(response=response)
