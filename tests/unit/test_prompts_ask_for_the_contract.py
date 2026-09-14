"""A phase prompt asks for the reply its caller reads, never for artefact bodies.

PROMPT.md told every phase agent to "Return each artefact's content as JSON" and
listed the artefacts to "Produce", while the runtime builds the artefacts itself
and reads only the Report's summary fields. MiniMax happened to add a summary;
nemotron-3-ultra followed the prompt, returned T02-T05 bodies, failed the contract
twice and pushed Phase 1 of case 02 to its deterministic fallback (2026-09-13).
"""
from __future__ import annotations

import pytest

from aaa.platform.prompt_registry.extract_agent_section import load_prompt

#: Prompt name → the keys its caller passes as ``contract=``.
CONTRACTS = {
    "phase1_scope": ("summary", "rationale_summary"),
    "phase2_data": ("summary", "rationale_summary"),
    "phase3_model": ("summary", "rationale_summary"),
    "phase4_output": ("summary", "rationale_summary"),
    "phase5_governance": ("summary", "phase5_narrative_summary"),
    "phase6_report": ("executive_summary", "summary", "rationale_summary"),
}
_BODY_REQUESTS = ("Return each artefact's content as JSON", "returned as JSON; the runtime renders",
                  "Produce ALL of the following")


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_the_prompt_names_a_contract_key_and_asks_for_no_artefact_body(name: str) -> None:
    prompt = load_prompt(name)
    assert any(f'"{key}"' in prompt for key in CONTRACTS[name]), name
    assert not [phrase for phrase in _BODY_REQUESTS if phrase in prompt], name
