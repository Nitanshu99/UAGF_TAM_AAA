"""Fix 11 (finding F9): the Orchestrator prompt must describe the real contract.

F9's root cause was drift, not a wrong instruction: when sequencing moved to the
bounded ReAct contract, the new ``## OUTPUT FORMAT`` section was *appended* and the
superseded ``## DISPATCH MESSAGE FORMAT`` / ``## COMPLIANCE MATRIX ASSEMBLY``
sections were left standing. Nothing tested prompt/contract agreement, so ~40% of
the system prompt went on ordering an emit shape the parser discards and a
derivation the runtime owns — invisibly, for as long as nobody read the prompt end
to end.

These tests are the missing check. They assert against the *loaded* prompt
(`load_prompt("orchestrator")`), which is what the model actually receives, and
against the parser itself rather than against a transcription of it, so a future
edit to either side that separates them fails here.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from aaa.agents.tier1.orchestrator.react import ACTIONS, DISPATCHABLE_PHASES
from aaa.platform.prompt_registry import load_prompt

_REACT = Path(__file__).resolve().parents[2] / "aaa/agents/tier1/orchestrator/react"

#: a line that declares a JSON field the model is being shown how to emit.
_EMIT_FIELD = re.compile(r'^\s*"([a-z_]+)"\s*:')

#: sections the Orchestrator system prompt is allowed to contain. An added
#: section is not a failure in itself — it is a prompt whose contract nobody has
#: checked, which is the state F9 found.
_EXPECTED_SECTIONS = (
    "## ROLE",
    "## RESPONSIBILITIES",
    "## CRITICAL GATES",
    "## TOOLS — RUN BY THE LOOP, NOT CALLED BY YOU",
    "## OUTPUT FORMAT — ONE DECISION PER REPLY (BINDING)",
    "## CONSTRAINTS",
)

#: fields of the Dispatch envelope the prompt used to order the model to emit.
#: The runtime builds the Dispatch; ``parse_decision`` reads none of these.
_SUPERSEDED_EMIT_FIELDS = (
    "message_type", "evidence_uris", "output_contract", "declaration_summary",
    "declared_modality", "declared_risk_tier", "declared_annex_iii_sections",
    "is_llm_or_agentic", "rerun_context",
)


@pytest.fixture(name="prompt", scope="module")
def _prompt() -> str:
    return load_prompt("orchestrator")


def _sections(prompt: str) -> dict[str, str]:
    """Split *prompt* into its ``## `` sections, heading → body."""
    parts = re.split(r"^(## .*)$", prompt, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def _output_format(prompt: str) -> str:
    section = _sections(prompt).get("## OUTPUT FORMAT — ONE DECISION PER REPLY (BINDING)")
    assert section, "the binding OUTPUT FORMAT section is gone"
    return section


def _emit_fields(text: str) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := _EMIT_FIELD.match(line))]


def _keys_read_by_the_parser() -> set[str]:
    """Every string literal the decision parser reads off the model's reply.

    Collected from the AST of ``decisions.py`` and ``shapes.py`` — the two
    modules between them are ``parse_decision`` — rather than from a list kept
    here, which would drift exactly as the prompt did.
    """
    keys: set[str] = set()
    for name in ("decisions.py", "shapes.py"):
        tree = ast.parse((_REACT / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            is_get = (isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute)
                      and node.func.attr == "get"
                      and node.args
                      and isinstance(node.args[0], ast.Constant)
                      and isinstance(node.args[0].value, str))
            if is_get:
                keys.add(node.args[0].value)
            if (isinstance(node, ast.Subscript)
                    and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)):
                keys.add(node.slice.value)
    return keys


# --------------------------------------------------------------------------- #
# suggestion 2, first half — every field the prompt names is a field that is read
# --------------------------------------------------------------------------- #

def test_every_field_the_output_format_names_is_read_by_the_parser(prompt):
    """A field the model is told to emit and nothing consumes is a lie in the prompt."""
    named = _emit_fields(_output_format(prompt))
    assert named, "the OUTPUT FORMAT block no longer shows the decision object"
    unread = sorted(set(named) - _keys_read_by_the_parser())
    assert not unread, f"prompt names fields parse_decision never reads: {unread}"


def test_the_output_format_names_every_field_the_decision_carries(prompt):
    """The converse: a field the parser reads and the prompt hides is unreachable."""
    named = set(_emit_fields(_output_format(prompt)))
    assert named == {"action", "phase_id", "task_brief", "rationale"}


def test_the_action_enum_is_exactly_the_parser_vocabulary(prompt):
    """F8 was an action the prompt demanded and the vocabulary lacked."""
    enum_line = next(line for line in _output_format(prompt).splitlines()
                     if line.strip().startswith('"action"'))
    offered = tuple(re.findall(r'"([A-Z_]+)"', enum_line))
    assert offered == ACTIONS


def test_every_dispatchable_phase_token_is_offered(prompt):
    """A phase the model may not name is a phase the runtime will never be asked for."""
    block = _output_format(prompt)
    for phase in DISPATCHABLE_PHASES:
        assert re.search(rf"\b{phase}\b", block), f"{phase} is not offered to the model"


# --------------------------------------------------------------------------- #
# suggestion 2, second half — no *other* emit-format block exists
# --------------------------------------------------------------------------- #

def test_no_emit_format_block_exists_outside_the_binding_output_format(prompt):
    """The F9 failure mode itself: two emit shapes, one of them discarded."""
    binding = "## OUTPUT FORMAT — ONE DECISION PER REPLY (BINDING)"
    stray = {heading: _emit_fields(body)
             for heading, body in _sections(prompt).items()
             if heading != binding and _emit_fields(body)}
    assert not stray, f"a second emit format is being shown to the model: {stray}"


def test_the_superseded_dispatch_envelope_is_gone(prompt):
    """The runtime assembles the Dispatch; the model chooses a phase."""
    for field in _SUPERSEDED_EMIT_FIELDS:
        assert f'"{field}"' not in prompt, f"{field} is still shown as a field to emit"
    assert "DISPATCH MESSAGE FORMAT" not in prompt
    assert "emit exactly this JSON" not in prompt


def test_the_prompt_does_not_hand_the_model_runtime_owned_derivations(prompt):
    """``node_compliance_matrix`` derives the verdicts, deterministically, in Python."""
    assert "COMPLIANCE MATRIX ASSEMBLY" not in prompt
    assert "derive_verdict" not in prompt


def test_the_sections_are_the_ones_this_test_has_checked(prompt):
    """An unreviewed section is how F9 arose; adding one must fail here first."""
    assert tuple(_sections(prompt)) == _EXPECTED_SECTIONS


# --------------------------------------------------------------------------- #
# what the deletions must not have taken with them
# --------------------------------------------------------------------------- #

def test_the_responsibilities_still_reach_the_runtime_they_describe(prompt):
    """Every action named in RESPONSIBILITIES must be one the loop executes."""
    body = _sections(prompt)["## RESPONSIBILITIES"]
    for action in ACTIONS:
        assert action in body, f"RESPONSIBILITIES never tells the model to emit {action}"
    assert "structured Dispatch message" not in body


def test_the_verdict_precedence_survived_the_deletion(prompt):
    """Deleted as an instruction, kept as what the model's sequencing will produce."""
    body = _sections(prompt)["## RESPONSIBILITIES"]
    for token in ("FAIL", "INSUFFICIENT_EVIDENCE", "PASS_WITH_OBSERVATIONS",
                  "DISCLAIMER_OF_OPINION", "insufficient_evidence_articles"):
        assert token in body
    assert body.index("is not yours to perform") < body.index("DISCLAIMER_OF_OPINION")
