"""JSONL persistence and response-field extraction for the LLM audit log."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: Dedicated JSONL audit file (one record per line, append mode).
_AUDIT_JSONL = Path("logs/audit/llm_audit.jsonl")


def _write_jsonl(record: dict[str, Any]) -> None:
    """Append one audit record to the JSONL file, creating dirs as needed."""
    _AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def _extract_text(response: Any) -> str:
    """Return the reply text of an LLM response, or an empty string."""
    try:
        return response.choices[0].message.content or ""
    except Exception:
        return ""


def _extract_usage(response: Any) -> dict[str, int]:
    """Return prompt/completion/total token counts (zeros when absent)."""
    try:
        u = response.usage
        return {
            "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
            "total_tokens": getattr(u, "total_tokens", 0) or 0,
        }
    except Exception:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
