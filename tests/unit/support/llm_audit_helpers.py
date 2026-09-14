"""Shared helpers for the llm_audit logger tests."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from unittest.mock import MagicMock


def make_mock_response(content="hello", prompt_tokens=10, completion_tokens=5):
    """Build a fake litellm response with usage counters."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.usage.prompt_tokens = prompt_tokens
    resp.usage.completion_tokens = completion_tokens
    resp.usage.total_tokens = prompt_tokens + completion_tokens
    return resp


def llm_audit_mod():
    """Import the llm_audit logger module (avoids name clash with the function)."""
    return importlib.import_module("aaa.observability.llm_audit.call_logger")


def jsonl_writer(audit_file: Path):
    """Return a ``_write_jsonl`` replacement that appends to *audit_file*."""
    def _write(record):
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        with audit_file.open("a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    return _write
