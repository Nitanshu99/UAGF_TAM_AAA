"""prompt_registry package (auto-split)."""
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
from aaa.platform.prompt_registry.prompt.version_hash import prompt_version_hash  # noqa: F401

__all__ = [
    '_PROMPT_PATH',
    '_PREAMBLE_PLACEHOLDER',
    '_AGENT_SECTION_PATTERNS',
    '_TIER3_PATTERNS',
    '_HITL_ESCALATION_PROMPT',
    '_read_prompt_markdown',
    '_extract_shared_preamble',
    '_extract_agent_section',
    '_extract_system_prompt_from_section',
    '_materialize_prompt',
    '_load_direct_prompt',
    '_compose_tier3_prompt',
    'load_prompt',
    'prompt_version_hash',
]
