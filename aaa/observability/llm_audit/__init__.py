"""aaa.observability.llm_audit — Auditable LLM call logger.

Every LLM call made through BaseAgent is wrapped by this module.  Each
invocation emits a structured JSON record (call id, engagement, agent,
model, full prompt and reply, token usage, estimated cost, latency, and
status) to ``logs/audit/llm_audit.jsonl`` in addition to the structlog
stream.
"""
from __future__ import annotations

from aaa.observability.llm_audit.call_logger import LLMAuditLogger
from aaa.observability.llm_audit.context import llm_audit

__all__ = ["LLMAuditLogger", "llm_audit"]
