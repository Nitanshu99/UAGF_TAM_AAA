"""
aaa.observability.llm_audit — Auditable LLM call logger.

Every LLM call made through BaseAgent is wrapped by this module.
Each invocation emits a structured JSON record containing:

  - call_id       : UUID for the individual call
  - engagement_id : current engagement (if bound via contextvars)
  - agent_name    : originating agent
  - model         : LiteLLM model string
  - messages      : full prompt sent to the model
  - response_text : full text content of the model reply
  - prompt_tokens / completion_tokens / total_tokens
  - estimated_cost_usd : derived from litellm.completion_cost when available
  - latency_ms    : wall-clock latency in milliseconds
  - status        : "ok" | "error"
  - error         : exception repr on failure

Records are written to ``logs/audit/llm_audit.jsonl`` (append, rotated
alongside the regular log file) in addition to the structlog stream.
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import structlog

_audit_logger = structlog.get_logger("aaa.observability.llm_audit")

# Dedicated JSONL audit file (one record per line, append mode)
_AUDIT_JSONL = Path("logs/audit/llm_audit.jsonl")


def _ensure_audit_file() -> None:
    _AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)


def _write_jsonl(record: dict[str, Any]) -> None:
    _ensure_audit_file()
    with _AUDIT_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def _extract_cost(response: Any) -> float | None:
    """Try to read cost from litellm response._hidden_params or compute it."""
    try:
        import litellm  # type: ignore

        return litellm.completion_cost(completion_response=response)
    except Exception:
        return None


def _extract_text(response: Any) -> str:
    try:
        return response.choices[0].message.content or ""
    except Exception:
        return ""


def _extract_usage(response: Any) -> dict[str, int]:
    try:
        u = response.usage
        return {
            "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
            "total_tokens": getattr(u, "total_tokens", 0) or 0,
        }
    except Exception:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


class LLMAuditLogger:
    """Context manager / async context manager that wraps one LLM call."""

    def __init__(
        self,
        agent_name: str,
        model: str,
        messages: list[dict[str, str]],
        engagement_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.call_id = str(uuid.uuid4())
        self.agent_name = agent_name
        self.model = model
        self.messages = messages
        self.engagement_id = engagement_id
        self.extra = extra or {}
        self._start: float = 0.0

    def _build_record(
        self,
        response: Any = None,
        error: BaseException | None = None,
    ) -> dict[str, Any]:
        elapsed_ms = round((time.perf_counter() - self._start) * 1000, 1)
        record: dict[str, Any] = {
            "call_id": self.call_id,
            "engagement_id": self.engagement_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "messages": self.messages,
            "latency_ms": elapsed_ms,
            "status": "ok" if error is None else "error",
            **self.extra,
        }
        if response is not None:
            record["response_text"] = _extract_text(response)
            record.update(_extract_usage(response))
            record["estimated_cost_usd"] = _extract_cost(response)
        if error is not None:
            record["error"] = repr(error)
        return record

    def start(self) -> None:
        self._start = time.perf_counter()

    def finish(self, response: Any = None, error: BaseException | None = None) -> None:
        record = self._build_record(response=response, error=error)
        _write_jsonl(record)
        if error:
            _audit_logger.error("llm_call_failed", **{k: v for k, v in record.items() if k != "messages"})
        else:
            _audit_logger.info("llm_call_ok", **{k: v for k, v in record.items() if k not in ("messages", "response_text")})


@asynccontextmanager
async def llm_audit(
    agent_name: str,
    model: str,
    messages: list[dict[str, str]],
    engagement_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> AsyncIterator[LLMAuditLogger]:
    """Async context manager wrapping a single LLM call with full audit logging."""
    auditor = LLMAuditLogger(
        agent_name=agent_name,
        model=model,
        messages=messages,
        engagement_id=engagement_id,
        extra=extra,
    )
    auditor.start()
    response = None
    try:
        yield auditor
    except Exception as exc:
        auditor.finish(error=exc)
        raise
    else:
        auditor.finish(response=response)
