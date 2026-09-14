"""Resolve the client's system prompt into the text the analyses ask for.

``decl["system_prompt_text"]`` was read in two places — the L-branch's injection
analysis and the CyberSecurity agent's specialist probes — and **written in
none**. A dead field of exactly the kind M10 describes: the client uploads
``system_prompt_uri``, it counts toward the 80 % completeness gate, the report
lists it, and the only two analyses that would read it are handed ``None``. Both
then reported "no system prompt supplied" for an engagement that supplied one.

A real one runs to kilobytes of instructions. Not reading it while auditing that
system for prompt-injection
resilience is the gap this closes.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Beyond this the prompt is truncated for the analysis; the full text stays in
#: the evidence store. Static analysis only needs the instructions themselves.
_MAX_CHARS = 20_000


def resolve_system_prompt(stage_b: dict[str, Any], store: Any) -> str | None:
    """Read ``system_prompt_uri`` as text.

    :param stage_b: The Annex IV dossier.
    :param store: Evidence store used to resolve ``minio://`` URIs.
    :returns: The prompt text, or ``None`` when absent or unreadable.
    """
    uri = stage_b.get("system_prompt_uri")
    if not uri:
        return None
    try:
        from aaa.platform.artifact_loader import load_artifact_from_uri
        content = load_artifact_from_uri(uri, store, "text")
    except Exception as exc:  # noqa: BLE001 — evidence is best-effort, never fatal
        logger.warning("system_prompt_uri %s could not be loaded: %s", uri, exc)
        return None
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    if not isinstance(content, str) or not content.strip():
        logger.warning("system_prompt_uri %s held no text; ignoring.", uri)
        return None
    return content[:_MAX_CHARS]
