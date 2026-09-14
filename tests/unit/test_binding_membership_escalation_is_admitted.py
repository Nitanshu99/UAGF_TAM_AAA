"""A material defect disputing what binding_articles lists does not block admission (T-20260915-001).

The fresh-clone rehearsal of case 06 had the Verifier call T14's scope statement wrong —
the articles it names "ARE in binding_articles" — as a material defect, while the list in
the same request held none of them; T14 went unadmitted where the matched runs admitted it.
Synthetic engagement: high tier, the self-assessment mapping Art.16 and Art.73.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.unfounded import downgrade_unfounded_escalation
from aaa.agents.tier2.governance_agent.scope_note import cgsa_scope_note
from aaa.tools.regulatory_coverage.binding import binding_articles
from aaa.tools.regulatory_coverage.unbound_note import stated_unbound

_TID = "T14_governance_findings"
_STATE = {"risk_tier": "high"}
_PAYLOAD = {"eu_ai_act_compliance_matrix": {"article_9": {}, "article_16": {}, "article_73": {}}}


def _content() -> dict:
    scope = {"risk_tier": "high", "binding_articles": binding_articles(_STATE)}
    return {"phase5_narrative_summary": f"Composite maturity is low.{cgsa_scope_note(_PAYLOAD, scope)}"}


def _issue(field: str, description: str, articles: list[str] | None = None) -> dict:
    issue = {"issue_type": "artefact_defect", "materiality": "material", "severity": "major",
             "field": field, "description": description}
    return {**issue, "articles": articles} if articles else issue


def _run(*issues: dict, accuracy: int = 2) -> tuple[str, dict]:
    state = {**_STATE, "verifier_critiques": {_TID: {
        "verdict": "escalate_hitl", "issues": list(issues), "scores": {"factual_accuracy": accuracy}}}}
    verdict = downgrade_unfounded_escalation(state, _TID, "escalate_hitl", "Phase 5", _content())
    return verdict, state["verifier_critiques"][_TID]


_DISPUTE = _issue("phase5_narrative_summary", "The narrative states Art.16 and Art.73 are not "
                  "among binding_articles; they ARE in binding_articles.", ["Art.16", "Art.73"])


def test_the_statement_round_trips() -> None:
    """The gate reads back exactly the articles Phase 5 wrote."""
    assert stated_unbound(_content()["phase5_narrative_summary"]) == ["Art.16", "Art.73"]


def test_a_refuted_dispute_and_an_uncontracted_field_admit_with_both_reasons() -> None:
    """The rehearsal's two material defects: the dispute and ``evidence_linkage``."""
    verdict, critique = _run(_DISPUTE, _issue("evidence_linkage (artefact-wide)", "No URIs."))
    assert verdict == "accept_with_notes" == critique["verdict"]
    assert "contain none of them" in critique["notes"][0]
    assert "does not define (evidence_linkage)" in critique["notes"][1]


def test_articles_parsed_from_the_description_when_none_are_listed() -> None:
    """Without an ``articles`` list the description's references decide."""
    assert _run(_issue("phase5_narrative_summary", "Art.16 is in binding_articles."))[0] == \
        "accept_with_notes"


def test_a_binding_article_another_field_or_a_factual_failure_keeps_the_escalation() -> None:
    """Art.9 binds; the note is not on ``domains``; accuracy 0 is never downgraded."""
    assert _run(_issue("phase5_narrative_summary", "Art.9 is not among binding_articles.",
                       ["Art.9"]))[0] == "escalate_hitl"
    assert _run(_issue("domains", "Art.16 is in binding_articles.", ["Art.16"]))[0] == \
        "escalate_hitl"
    assert _run(_DISPUTE, accuracy=0)[0] == "escalate_hitl"
    assert _run(_DISPUTE, _issue("phase5_narrative_summary", "Wrong maturity."))[0] == \
        "escalate_hitl"
