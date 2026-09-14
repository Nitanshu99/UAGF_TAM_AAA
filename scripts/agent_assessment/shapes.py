"""Summarising one call's payload shape and its retrieval, for the digest."""
from __future__ import annotations

import hashlib
import json

#: Payload keys worth reporting a size or count for rather than a value.
_BULK = ("regulatory_hits", "client_doc_hits", "tool_outputs", "phase_artefacts",
         "verifier_critiques", "blocking_findings", "compliance_matrix", "probes")
#: A reply shorter than this is almost always a refusal, a plan, or a stub.
SHORT_REPLY = 400
def _sections(text: str) -> list[str]:
    """Markdown headings in an assembled system prompt, in order."""
    return [line.strip() for line in text.splitlines()
            if line.startswith("## ") and len(line) < 80]
def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
def _payload_shape(content: str) -> list[str]:
    """Describe a JSON user payload by key, with counts for the bulky parts."""
    try:
        payload = json.loads(content)
    except (TypeError, ValueError):
        return [f"(not JSON; {len(content):,} chars)"]
    if not isinstance(payload, dict):
        return [f"(JSON {type(payload).__name__}; {len(content):,} chars)"]
    out: list[str] = []
    for key, value in payload.items():
        if key in _BULK or isinstance(value, (list, dict)):
            size = len(value) if hasattr(value, "__len__") else "-"
            out.append(f"{key}[{size}]")
        elif value is None:
            out.append(f"{key}=null")
        else:
            text = str(value)
            out.append(f"{key}={text[:60]}" + ("…" if len(text) > 60 else ""))
    return out
def _retrieval(content: str) -> str:
    """Whether law and client documents actually reached this call."""
    try:
        payload = json.loads(content)
    except (TypeError, ValueError):
        return "n/a"
    if not isinstance(payload, dict):
        return "n/a"
    reg = payload.get("regulatory_hits") or []
    doc = payload.get("client_doc_hits") or []
    expansion = payload.get("retrieval_expansion") or {}
    note = ""
    if expansion:
        note = (" [closed]" if expansion.get("retrieval_closed")
                else f" [round {expansion.get('round')}"
                     f"{', FINAL' if expansion.get('final_round') else ''}]")
    return f"reg={len(reg)} doc={len(doc)}{note}"


__all__ = ["SHORT_REPLY", "_BULK", "_digest", "_payload_shape", "_retrieval", "_sections"]
