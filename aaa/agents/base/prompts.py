"""Prompt-provenance helpers bound onto BaseAgent."""
from __future__ import annotations

from typing import Any


def prompt_metadata(self, prompt_name: str,
                    llm_fallback_mode: bool | None = None) -> dict[str, Any]:
    """Return prompt provenance metadata for artefact embedding."""
    from aaa.platform.prompt_registry import prompt_version_hash

    metadata: dict[str, Any] = {
        "prompt_source": "PROMPT.md",
        "prompt_version_hash": prompt_version_hash(),
        "agent_prompt": prompt_name,
    }
    if llm_fallback_mode is not None:
        metadata["llm_fallback_mode"] = llm_fallback_mode
    return metadata

def prompt_note(self, prompt_name: str, llm_fallback_mode: bool) -> str:
    """Return a one-line provenance note appended to artefact narratives."""
    metadata = self.prompt_metadata(prompt_name, llm_fallback_mode)
    return (
        "Prompt metadata: "
        f"source={metadata['prompt_source']}, "
        f"agent_prompt={metadata['agent_prompt']}, "
        f"prompt_version_hash={metadata['prompt_version_hash']}, "
        f"llm_fallback_mode={str(llm_fallback_mode).lower()}."
    )
