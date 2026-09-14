"""The integrity gate must not discard a sound judgement over its wrapping.

``verifier/llm.py`` parsed its reply with strict ``json.loads`` while every
other agent went through ``acompletion_json`` and its lenient parser. The
Verifier is the worst place in the system to keep that difference: its failure
is silent by design — it falls back to a deterministic rubric that returns a
verdict looking exactly like a judged one.

On the 2026-09-10 GLM-5.3-Flash run **6 of 17** critiques were thrown away that
way. Every one was complete and well-reasoned; they arrived inside a markdown
fence, or with a sentence after the closing brace. Annex III, Art. 5 and Art. 6
lost their PASS because ``T02_system_card`` and ``T03_annex_iii_mapping`` went
unadmitted, and regulatory coverage fell 73.3% → 53.3%.
"""
from __future__ import annotations

import json

import pytest

from aaa.agents.base.json_utils import _loads_lenient

CRITIQUE = ('{"message_type": "Critique", "phase_id": "P1", '
            '"scores": {"factual_accuracy": 3, "completeness": 2}, '
            '"verdict": "ACCEPT_WITH_OBSERVATIONS", "issues": []}')


@pytest.mark.parametrize("wrapping,reply", [
    ("markdown fence", f"```json\n{CRITIQUE}\n```"),
    ("truncated fence", f"{CRITIQUE}\n``"),
    ("trailing prose", f"{CRITIQUE}\nTotal 12 → ACCEPT_WITH_OBSERVATIONS."),
    ("leading prose", f"Here is the critique:\n{CRITIQUE}"),
    ("bare", CRITIQUE),
])
def test_a_critique_survives_the_wrapping_it_arrives_in(wrapping, reply):
    """Each shape is one the run actually produced, or a near neighbour."""
    out = _loads_lenient(reply)
    assert out["verdict"] == "ACCEPT_WITH_OBSERVATIONS", wrapping
    assert out["message_type"] == "Critique"


def test_a_fragment_is_caught_by_the_caller_not_the_parser():
    """A fragment is worse than a refusal — but only the caller can tell.

    Call #09:36:09 of the assessed run decoded to its own ``scores`` sub-object:
    five plausible integers and no ``verdict``, reading downstream as a critique
    that reached no conclusion rather than one that never parsed. Refusing that
    in the parser, on position alone, also refused a *re-emitted* critique
    further down the same reply — the two are indistinguishable there. So the
    parser returns its widest reading and the Verifier rejects a verdict-less
    critique, which is the knowledge only it has.
    """
    broken = ('{"message_type": "Critique", "scores": {"factual_accuracy": 3}, '
              '"verdict": "RERUN", "issues": [],}')          # trailing comma
    out = _loads_lenient(broken)
    assert "verdict" not in out, "this is the fragment the Verifier must reject"

    # Behavioural, for the same reason as below: the Verifier must reject a
    # verdict-less fragment, wherever in the module that check happens to live.
    import asyncio

    from aaa.agents.tier1.verifier.llm import _critique_once

    class _Fragment:
        """Always returns the verdict-less fragment."""

        async def acompletion(self, **_kwargs):
            """Reply with a critique that reached no conclusion."""
            return type("R", (), {"choices": [type("C", (), {
                "message": type("M", (), {
                    "content": '{"scores": {"factual_accuracy": 3}}'})()})()]})()

    with pytest.raises(ValueError):
        asyncio.run(_critique_once(_Fragment(), [], "P1", "T03_annex_iii_mapping"))


def test_the_widest_match_wins_over_the_first():
    """Two decodable objects: the outer one is the answer."""
    text = 'prefix {"inner": 1} suffix {"message_type": "Critique", "verdict": "ACCEPT", "x": [1,2,3]}'
    assert _loads_lenient(text)["verdict"] == "ACCEPT"


def test_nothing_decodable_still_raises():
    """Silence is not an answer; the caller's fallback must still engage."""
    with pytest.raises(json.JSONDecodeError):
        _loads_lenient("no json here at all")


def test_empty_input_is_an_empty_object():
    """An empty reply is an empty object, not a parse error."""
    assert _loads_lenient("") == {}
    assert _loads_lenient("   ") == {}


def test_the_verifier_parses_leniently():
    """The call site must not reintroduce a strict parse.

    Asserted through behaviour, not through the source line. The earlier version
    matched ``_loads_lenient(resp.choices[0].message.content`` literally and
    broke the moment the call site was refactored to retry a truncated reply —
    while the leniency it guards was entirely intact. That is the failure mode
    the M1-M30 register records: guards that assert source text die on rewrites,
    guards that assert behaviour survive them.
    """
    import asyncio

    from aaa.agents.tier1.verifier.llm import _critique_once

    class _Agent:
        """Returns one fenced critique, the shape strict parsing rejected."""

        calls = 0

        async def acompletion(self, **_kwargs):
            """Reply once, inside a markdown fence."""
            type(self).calls += 1
            text = f"```json\n{CRITIQUE}\n```"
            return type("R", (), {"choices": [type("C", (), {
                "message": type("M", (), {"content": text})()})()]})()

    out = asyncio.run(_critique_once(_Agent(), [], "P1", "T03_annex_iii_mapping"))
    assert out["verdict"] == "ACCEPT_WITH_OBSERVATIONS"
    assert _Agent.calls == 1, "a fenced reply is readable; it must not be re-asked"
