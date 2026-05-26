"""
Prompt snapshot tests — pin the structure and key phrases of the message
builder so refactors that alter the wording become visible in PR diffs.

Why this matters
----------------
The compliance critique relies on the verbatim phrasing of the four-dimension
rubric inside ``_SYSTEM_PROMPT`` and the XML-tag framing in
``_build_critique_messages``.  Silent edits would change the behaviour of
every Tier-1/2 critique without any test failing.  These tests intentionally
hard-code the expected text; if you need to change a prompt, update both the
builder and the snapshot in the same commit.

Message structure (as of system+user split refactor)
-----------------------------------------------------
``_build_critique_messages`` returns::

    [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": "<phase>…</phase>\\n<template>…</template>\\n…"},
    ]

The system message is byte-identical across every call (cache-friendly).
All per-call variability lives in the user message inside XML data tags.
"""
from __future__ import annotations

from aaa.agents.tier1.verifier import _SYSTEM_PROMPT, _build_critique_messages

# ---------------------------------------------------------------------------
# Snapshot: user message — empty evidence URIs
# ---------------------------------------------------------------------------

_EMPTY_URIS_USER_SNAPSHOT = (
    "<phase>P1</phase>\n"
    "<template>T02_system_card</template>\n"
    "\n"
    "<evidence_uris>\n"
    "  (none)\n"
    "</evidence_uris>\n"
    "\n"
    "<artefact>\n"
    '{\"hello\": \"world\"}\n'
    "</artefact>"
)

# ---------------------------------------------------------------------------
# Snapshot: user message — two evidence URIs
# ---------------------------------------------------------------------------

_TWO_URIS_USER_SNAPSHOT = (
    "<phase>P6</phase>\n"
    "<template>T17_compliance_matrix</template>\n"
    "\n"
    "<evidence_uris>\n"
    "  - evidence://eng-001/p1/T02_system_card.json\n"
    "  - evidence://eng-001/p3/T11_robustness_report.json\n"
    "</evidence_uris>\n"
    "\n"
    "<artefact>\n"
    '{\"in_scope_articles\": [\"Art.9\", \"Art.10\"]}\n'
    "</artefact>"
)


# ---------------------------------------------------------------------------
# System-prompt stability (cache-friendliness)
# ---------------------------------------------------------------------------

def test_system_prompt_is_stable_across_calls():
    """system content must be byte-identical regardless of per-call args."""
    msgs_a = _build_critique_messages("P1", "T02", "{}", [])
    msgs_b = _build_critique_messages("P6", "T17", '{"x": 1}', ["ev://a"])
    assert msgs_a[0]["content"] == msgs_b[0]["content"], (
        "_SYSTEM_PROMPT changed between calls — breaks prompt-cache hits"
    )


def test_system_prompt_matches_module_constant():
    """The system message content must equal the exported _SYSTEM_PROMPT."""
    msgs = _build_critique_messages("P1", "T02", "{}", [])
    assert msgs[0]["content"] == _SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Message list structure
# ---------------------------------------------------------------------------

def test_messages_list_has_two_entries():
    msgs = _build_critique_messages("P1", "T02", "{}", [])
    assert len(msgs) == 2


def test_first_message_is_system():
    msgs = _build_critique_messages("P1", "T02", "{}", [])
    assert msgs[0]["role"] == "system"


def test_second_message_is_user():
    msgs = _build_critique_messages("P1", "T02", "{}", [])
    assert msgs[1]["role"] == "user"


# ---------------------------------------------------------------------------
# User-message snapshots
# ---------------------------------------------------------------------------

def test_user_message_no_evidence_uris():
    """Empty-URI branch renders the literal '(none)' placeholder."""
    msgs = _build_critique_messages(
        phase_id="P1",
        template_id="T02_system_card",
        content_str='{"hello": "world"}',
        evidence_uris=[],
    )
    assert msgs[1]["content"] == _EMPTY_URIS_USER_SNAPSHOT


def test_user_message_with_evidence_uris():
    """Two-URI branch renders one '  - <uri>' line per entry, in order."""
    msgs = _build_critique_messages(
        phase_id="P6",
        template_id="T17_compliance_matrix",
        content_str='{"in_scope_articles": ["Art.9", "Art.10"]}',
        evidence_uris=[
            "evidence://eng-001/p1/T02_system_card.json",
            "evidence://eng-001/p3/T11_robustness_report.json",
        ],
    )
    assert msgs[1]["content"] == _TWO_URIS_USER_SNAPSHOT


# ---------------------------------------------------------------------------
# XML delimiters
# ---------------------------------------------------------------------------

def test_user_message_wraps_artefact_in_xml_tags():
    """Untrusted artefact content must be enclosed in <artefact>…</artefact>."""
    content = '{"sensitive": "data"}'
    msgs = _build_critique_messages("P1", "T02", content, [])
    user = msgs[1]["content"]
    assert "<artefact>" in user
    assert "</artefact>" in user
    assert content in user


def test_user_message_wraps_evidence_in_xml_tags():
    """Evidence URIs must be enclosed in <evidence_uris>…</evidence_uris>."""
    msgs = _build_critique_messages("P1", "T02", "{}", ["ev://a"])
    user = msgs[1]["content"]
    assert "<evidence_uris>" in user
    assert "</evidence_uris>" in user


def test_uri_order_is_preserved():
    """The user message MUST list URIs in the order received (not sorted)."""
    msgs = _build_critique_messages(
        phase_id="P2",
        template_id="T06_datasheet_for_datasets",
        content_str="{}",
        evidence_uris=["evidence://b", "evidence://a", "evidence://c"],
    )
    user = msgs[1]["content"]
    block = user.split("<evidence_uris>\n", 1)[1].split("\n</evidence_uris>", 1)[0]
    assert block == "  - evidence://b\n  - evidence://a\n  - evidence://c"


# ---------------------------------------------------------------------------
# System-prompt content: rubric dimensions, CoT, security, output contract
# ---------------------------------------------------------------------------

def test_system_prompt_contains_four_rubric_dimensions():
    """All four rubric dimensions must be present in the system prompt."""
    for dim in (
        "factual_accuracy",
        "completeness",
        "evidence_linkage",
        "citation_correctness",
    ):
        assert dim in _SYSTEM_PROMPT, f"Rubric dimension '{dim}' missing from system prompt"


def test_system_prompt_contains_chain_of_thought_instruction():
    """System prompt must instruct the model to think step by step."""
    assert "step by step" in _SYSTEM_PROMPT.lower()


def test_system_prompt_contains_security_instruction():
    """System prompt must tell the model to treat artefact content as DATA."""
    assert "DATA" in _SYSTEM_PROMPT
    assert "<artefact>" in _SYSTEM_PROMPT


def test_system_prompt_demands_json_object_response():
    """Output contract must explicitly require a JSON object with 3 keys."""
    assert "Respond ONLY with a JSON object" in _SYSTEM_PROMPT
    assert "issues" in _SYSTEM_PROMPT
    assert "notes" in _SYSTEM_PROMPT
    assert "article_citations" in _SYSTEM_PROMPT
