"""Leaf-agent LLM synthesis: prompts load, narratives merge, fallbacks hold."""
from __future__ import annotations

from typing import Any

import pytest

from aaa.agents.tier1.regulatory_rag import RegulatoryRAG
from aaa.agents.tier3.cyber_agent.llm import run_llm_synthesis as cyber_synth
from aaa.agents.tier3.cyber_agent.llm import with_narrative
from aaa.agents.tier3.privacy_agent.llm import run_llm_synthesis as privacy_synth
from aaa.agents.tier3.uagf_tam_l.llm import run_llm_synthesis as tam_l_synth
from aaa.platform.prompt_registry import load_prompt


class FakeAgent:
    """Returns a canned JSON reply, or raises when ``fail`` is set."""

    def __init__(self, reply: dict[str, Any] | None = None, fail: bool = False):
        self._reply, self._fail = reply or {}, fail

    async def acompletion_json(self, prompt_name: str, payload: Any,
                               **_: Any) -> dict[str, Any]:
        """Return the canned reply for any prompt."""
        if self._fail:
            raise RuntimeError("provider down")
        self._reply.setdefault("_prompt", prompt_name)
        return self._reply

    def prompt_note(self, prompt_name: str, fallback: bool) -> str:
        """Mimic BaseAgent's provenance note."""
        return f"[prompt={prompt_name} fallback={fallback}]"


def test_individual_tier3_prompts_load_from_prompt_md():
    """The new registry keys resolve to non-empty PROMPT.md sections."""
    for name in ("uagf_tam_l", "cyber", "privacy", "regulatory_rag"):
        text = load_prompt(name)
        assert "ROLE" in text or len(text) > 200


def _rag(hits: list[dict[str, Any]]) -> RegulatoryRAG:
    """A RegulatoryRAG whose retrieval is stubbed; nothing else is faked."""
    rag = RegulatoryRAG()
    rag.search = lambda query, top_k=3: hits            # type: ignore[method-assign]
    return rag


async def test_the_rag_returns_passages_and_makes_no_llm_call():
    """`process` is a formatted view of `search` — retrieval, not generation.

    It used to synthesise: a model condensed the passages into prose, which put
    a second model between the corpus and the auditor. `acompletion_json` is
    replaced with a raiser here, so a reply that came from a model rather than
    from the corpus fails the test rather than passing it quietly.
    """
    rag = _rag([{"text": "A risk management system shall be established.",
                 "source": "EU AI Act Article 9", "locator": "euaiact://Article_9"}])

    async def _explode(*_: Any, **__: Any) -> dict[str, Any]:
        raise AssertionError("process must not call an LLM")

    rag.acompletion_json = _explode                      # type: ignore[method-assign]
    out = await rag.process("risk management system")
    assert out == ("EU AI Act Article 9 [euaiact://Article_9]: "
                   "A risk management system shall be established.")


async def test_every_passage_carries_its_pinpoint():
    """A quote without its locator is not citable, which is the whole point."""
    out = await _rag([
        {"text": "First.", "source": "EU AI Act Article 10", "locator": "euaiact://Article_10"},
        {"text": "Second.", "source": "EU AI Act Article 72", "locator": "euaiact://Article_72"},
    ]).process("q")
    assert "euaiact://Article_10" in out and "euaiact://Article_72" in out
    assert out.count("\n\n") == 1


async def test_an_empty_corpus_says_so_rather_than_returning_nothing():
    """Silence is what F1 was; a miss is stated."""
    assert await _rag([]).process("unicorns") == "No regulatory passage found for: unicorns"


def test_the_synthesis_module_is_gone():
    """A deleted path must not be importable, or it will be wired back in."""
    with pytest.raises(ModuleNotFoundError):
        __import__("aaa.agents.tier1.regulatory_rag.llm")


@pytest.mark.parametrize("synth,reply_key", [
    (cyber_synth, "security_narrative"),
    (privacy_synth, "privacy_narrative"),
    (tam_l_synth, "evaluation_narrative"),
])
async def test_tier3_synthesis_narrative_and_fallback(synth, reply_key):
    """Each tier-3 synthesis yields a narrative, and labels its fallback."""
    args = {cyber_synth: ({}, [], None, []), privacy_synth: ({}, {}, []),
            tam_l_synth: ({}, {})}[synth]
    narrative, note = await synth(FakeAgent({reply_key: "interpreted"}), *args)
    assert narrative == "interpreted"
    assert "fallback=False" in note
    narrative, note = await synth(FakeAgent(fail=True), *args)
    assert narrative is None
    assert "fallback=True" in note


def test_with_narrative_annotates_artefact():
    """with_narrative attaches narrative+note, or note alone in fallback."""
    art = with_narrative({}, "risk interpreted", "[note]")
    assert art["tier3_llm_narrative"] == "risk interpreted [note]"
    art = with_narrative({}, None, "[note]")
    assert art["tier3_llm_narrative"] == "[note]"
