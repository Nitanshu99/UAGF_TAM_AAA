"""Part 2 of the former ``prompt_registry`` module (auto-split)."""
from __future__ import annotations

import re

from aaa.platform.prompt_registry.prompt.path import (  # noqa: F401
    _AGENT_SECTION_PATTERNS,
    _HITL_ESCALATION_PROMPT,
    _PREAMBLE_PLACEHOLDER,
    _PROMPT_PATH,
    _TIER3_PATTERNS,
    _extract_shared_preamble,
    _read_prompt_markdown,
)


def _extract_agent_section(markdown: str, heading_pattern: str) -> str:
    heading_re = re.compile(heading_pattern, flags=re.MULTILINE)
    heading_match = heading_re.search(markdown)
    if not heading_match:
        raise KeyError(f"Prompt section not found for pattern: {heading_pattern}")
    next_heading_re = re.compile(r"^### Agent \d+ — .*?$", flags=re.MULTILINE)
    next_heading = next_heading_re.search(markdown, heading_match.end())
    end = next_heading.start() if next_heading else len(markdown)
    return markdown[heading_match.start():end]


def _extract_system_prompt_from_section(section: str) -> str:
    if "#### SYSTEM PROMPT" not in section:
        raise ValueError("Section does not contain a SYSTEM PROMPT block")
    system_part = section.split("#### SYSTEM PROMPT", 1)[1]
    code_match = re.search(r"```\n(.*?)\n```", system_part, flags=re.DOTALL)
    if not code_match:
        raise ValueError("SYSTEM PROMPT code block not found")
    return code_match.group(1).strip()


def _materialize_prompt(prompt_text: str, shared_preamble: str) -> str:
    return prompt_text.replace(_PREAMBLE_PLACEHOLDER, shared_preamble).strip()


def _load_direct_prompt(markdown: str, prompt_name: str, shared_preamble: str) -> str:
    section = _extract_agent_section(markdown, _AGENT_SECTION_PATTERNS[prompt_name])
    return _materialize_prompt(_extract_system_prompt_from_section(section), shared_preamble)


def _compose_tier3_prompt(markdown: str, shared_preamble: str) -> str:
    parts: list[str] = []
    for label, pattern in _TIER3_PATTERNS:
        section = _extract_agent_section(markdown, pattern)
        prompt = _materialize_prompt(_extract_system_prompt_from_section(section), shared_preamble)
        parts.append(f"## {label}\n{prompt}")
    return "\n\n".join(parts).strip()


def load_prompt(agent_name: str) -> str:
    """Return the system prompt for *agent_name* from ``PROMPT.md``."""
    markdown = _read_prompt_markdown()
    shared_preamble = _extract_shared_preamble(markdown)

    if agent_name in _AGENT_SECTION_PATTERNS:
        return _load_direct_prompt(markdown, agent_name, shared_preamble)
    if agent_name == "tier3_specialist":
        return _compose_tier3_prompt(markdown, shared_preamble)
    if agent_name == "hitl_escalation":
        return _HITL_ESCALATION_PROMPT
    raise KeyError(f"Unknown prompt name: {agent_name}")
