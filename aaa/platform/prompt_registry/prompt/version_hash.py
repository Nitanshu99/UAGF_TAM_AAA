"""Part 3 of the former ``prompt_registry`` module (auto-split)."""
from __future__ import annotations

import hashlib

from aaa.platform.prompt_registry.extract_agent_section import (  # noqa: F401
    _compose_tier3_prompt,
    _extract_agent_section,
    _extract_system_prompt_from_section,
    _load_direct_prompt,
    _materialize_prompt,
    load_prompt,
)
from aaa.platform.prompt_registry.prompt.path import (  # noqa: F401
    _AGENT_SECTION_PATTERNS,
    _HITL_ESCALATION_PROMPT,
    _PREAMBLE_PLACEHOLDER,
    _PROMPT_PATH,
    _TIER3_PATTERNS,
    _extract_shared_preamble,
    _read_prompt_markdown,
)


def prompt_version_hash() -> str:
    """Return a SHA-256 hash of ``PROMPT.md`` for provenance tracking."""
    return hashlib.sha256(_read_prompt_markdown().encode("utf-8")).hexdigest()


__all__ = ["load_prompt", "prompt_version_hash"]
