"""Every tier-3 spawn asks for the client's documents, and none can forget to.

M13 wired dossier search into two of the three spawns; the L-branch passed no
query, so on every Mariposa run it was told it had no retrieval channel while the
dossier held its system prompt, RAG manifest and guardrail configuration
(T-20260913-029).
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
from typing import Any

import pytest

from aaa.agents.tier3 import narrative

_SPAWNS = {
    "aaa.agents.tier3.uagf_tam_l.llm": lambda m: m.run_llm_synthesis(object(), _DECL, {}),
    "aaa.agents.tier3.cyber_agent.llm": lambda m: m.run_llm_synthesis(object(), _DECL, [], None, []),
    "aaa.agents.tier3.privacy_agent.llm": lambda m: m.run_llm_synthesis(object(), _DECL, *_privacy_args(m)),
}
_DECL = {"engagement_id": "eng-x"}


def _privacy_args(module: Any) -> list[Any]:
    """Placeholder positional arguments for the privacy spawn's own signature."""
    params = list(inspect.signature(module.run_llm_synthesis).parameters)[2:]
    return [None] * len(params)


@pytest.mark.parametrize("module_name", sorted(_SPAWNS))
def test_the_spawn_passes_its_engagement_and_a_query(monkeypatch: pytest.MonkeyPatch,
                                                     module_name: str) -> None:
    """A non-empty query and the engagement id reach the narrative helper."""
    module = importlib.import_module(module_name)
    seen: dict[str, Any] = {}

    async def _capture(*_a: Any, **kwargs: Any) -> tuple[None, str]:
        seen.update(kwargs)
        return None, ""

    monkeypatch.setattr(module, "run_narrative_synthesis", _capture)
    asyncio.run(_SPAWNS[module_name](module))
    assert seen["engagement_id"] == "eng-x"
    assert seen["client_doc_query"].strip()


def test_omitting_the_query_is_an_error_not_a_silent_skip() -> None:
    """The defaults are gone, so a new spawn cannot quietly search nothing."""
    params = inspect.signature(narrative.run_narrative_synthesis).parameters
    assert params["engagement_id"].default is inspect.Parameter.empty
    assert params["client_doc_query"].default is inspect.Parameter.empty
