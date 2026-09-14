"""The remaining "what it leaves open" items, closed or asserted.

Each of these was recorded in a remediation log as a residual. They are gathered
here because they are one-assertion facts rather than fixes, and because a
residual with no test is a residual that quietly stops being true.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# fix 40 / fix 41 — "`prohibited` resolves to an empty set", assumed unverified
# --------------------------------------------------------------------------- #

def test_a_prohibited_engagement_never_reaches_the_matrix():
    """Flagged twice as an unverified assumption. It holds, and here is why.

    `halt_engagement` raises `IntakeValidatorError` in Stage A — before T01a is
    even stored — so a prohibited engagement stops at intake and the empty
    `ARTICLE_SET["prohibited"]` is never handed to `_derive_verdicts`.
    """
    from aaa.agents.intake_validator.errors import IntakeValidatorError
    from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET

    assert ARTICLE_SET["prohibited"] == frozenset()
    source = Path("aaa/agents/intake_validator/stage/a.py").read_text()
    halt = source.split('if gate.get("halt_engagement"):', 1)[1][:200]
    assert "raise IntakeValidatorError" in halt
    assert "store_artefact" not in halt, "the halt must precede the first write"
    assert issubclass(IntakeValidatorError, Exception)


def test_the_csp_planner_also_skips_every_phase_when_prohibited():
    """Belt and braces: even if intake let one through, nothing would run."""
    from aaa.tools.csp_solver import solve_phase_plan

    plan = solve_phase_plan({"risk_tier": "prohibited", "modality": "tabular",
                             "is_llm_or_agentic": False, "annex_iii_mapping": [],
                             "special_category_data": False})
    assert all(plan[p] == "S" for p in ("P2", "P3", "P4", "P5", "L", "CYBER", "PRIV"))


# --------------------------------------------------------------------------- #
# fix 46 — "`request_timeout` is 6000 s and is the only ceiling nobody audited"
# --------------------------------------------------------------------------- #

def test_nothing_in_this_codebase_relies_on_litellms_module_level_timeout():
    """It is 6000 s, and every call carries its own explicit ceiling instead."""
    import litellm

    assert litellm.request_timeout == 6000.0, "if this moves, so does the argument"
    offenders = [
        f"{p}:{n}" for p in Path("aaa").rglob("*.py")
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if "request_timeout" in line
    ]
    assert not offenders, f"something reads litellm's module ceiling: {offenders}"


@pytest.mark.asyncio
async def test_every_call_carries_an_explicit_ceiling_so_6000_never_binds():
    from unittest.mock import AsyncMock, MagicMock, patch

    from tests.unit.support.flex_retry_helpers import flex_module, ok_response

    mock = MagicMock()
    mock.acompletion = AsyncMock(return_value=ok_response())
    with patch.dict("sys.modules", {"litellm": mock}):
        await flex_module().flex_acompletion(model="m", messages=[])
    passed = mock.acompletion.call_args.kwargs["timeout"]
    assert passed is not None and passed < 6000.0


# --------------------------------------------------------------------------- #
# fix 39 — "`LLMAuditLogger` does not record `attempts`"
# --------------------------------------------------------------------------- #

def test_both_audit_writers_record_the_same_attempt_field(tmp_path, monkeypatch):
    """The shape drift `aaa/agents/base/audit.py` warns about, closed."""
    from aaa.platform.transient_retry import record_attempts
    from tests.unit.support.llm_audit_helpers import jsonl_writer, llm_audit_mod, make_mock_response

    mod = llm_audit_mod()
    out = tmp_path / "llm_audit.jsonl"
    monkeypatch.setattr(mod, "_write_jsonl", jsonl_writer(out))

    auditor = mod.LLMAuditLogger(agent_name="Verifier", model="m", messages=[])
    auditor.start()
    auditor.finish(response=make_mock_response("pong"))

    with record_attempts() as retried:
        retried.append("ServiceUnavailableError('overloaded')")
        second = mod.LLMAuditLogger(agent_name="Verifier", model="m", messages=[])
        second.start()
        second.finish(response=make_mock_response("pong"))

    records = [json.loads(line) for line in out.read_text().splitlines() if line]
    assert records[0]["attempts"] == 1
    assert "retried_after" not in records[0]
    assert records[1]["attempts"] == 2
    assert "overloaded" in records[1]["retried_after"][0]


# --------------------------------------------------------------------------- #
# fix 43 — "only one level of nesting is handled"
# --------------------------------------------------------------------------- #

def test_no_article_anywhere_nests_more_than_one_level():
    """`core_article` reduces one level; a deeper chain would read as a plain
    article and be reconciled with nothing. Nothing emits one — asserted so that
    if something starts to, this fails rather than the report going quiet."""
    from aaa.tools.regulatory_coverage.artefact_contract import ARTEFACT_ARTICLES
    from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET
    from aaa.tools.regulatory_coverage.engagement_scope import core_article

    every = {a for arts in ARTEFACT_ARTICLES.values() for a in arts}
    every |= {a for arts in ARTICLE_SET.values() for a in arts}
    for article in every:
        assert core_article(core_article(article)) == core_article(article), (
            f"{article} would need more than one reduction")
        assert article.count("§") <= 1, f"{article} nests deeper than one level"


# --------------------------------------------------------------------------- #
# fixes 26/35, 40, 50 — three records the audit kept and no reader saw
# --------------------------------------------------------------------------- #

def test_the_hitl_packet_carries_what_the_audit_noticed_about_itself():
    """`over_cited_articles` was recorded and unread; so were its two siblings."""
    from aaa.tools.hitl_review import build_hitl_review_packet

    state = {
        "engagement_id": "eng-t", "hitl_required": True,
        "verifier_critiques": {}, "phase_artefacts": {}, "blocking_findings": [],
        "unadmitted_artefacts": [{"template_id": "T11_robustness_report",
                                  "verdict": "unverified", "articles": ["Art.15"]}],
        "out_of_scope_claims": [{"article": "Art.9", "claimed_by": "Phase 5",
                                 "risk_tier": "limited"}],
        "over_cited_articles": [{"template_id": "T13_output_sampling_log",
                                 "article": "Art.15§1",
                                 "contract": ["Art.10§2(f)"]}],
    }
    packet = build_hitl_review_packet(state)
    book = packet["audit_bookkeeping"]
    assert book["unadmitted_artefacts"][0]["template_id"] == "T11_robustness_report"
    assert book["out_of_scope_claims"][0]["article"] == "Art.9"
    assert book["over_cited_articles"][0]["article"] == "Art.15§1"


def test_an_engagement_with_nothing_to_report_carries_empty_lists():
    """Present and empty, so a reviewer can tell 'none' from 'not recorded'."""
    from aaa.tools.hitl_review import build_hitl_review_packet

    packet = build_hitl_review_packet(
        {"engagement_id": "eng-t", "hitl_required": True, "verifier_critiques": {},
         "phase_artefacts": {}, "blocking_findings": []})
    assert packet["audit_bookkeeping"] == {"unadmitted_artefacts": [],
                                           "out_of_scope_claims": [],
                                           "over_cited_articles": []}
