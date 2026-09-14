"""Part 8 of the former ``compliance_matrix`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (  # noqa: F401
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import (  # noqa: F401
    _cgsa_controls_for,
    _findings_by_article,
)
from aaa.agents.tier1.phases.compliance_matrix.logger import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _CORE_HIGH_RISK_ARTICLES,
    _TEMPLATE_ARTICLES,
    _core_article,
    logger,
)
from aaa.agents.tier1.phases.compliance_matrix.rationale import _rationale  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import (  # noqa: F401
    _article_verdict,
    _supporting_tids,
)
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION, FAIL, PASS, PASS_WITH_OBSERVATIONS


def _compute_final_verdict(state: dict) -> str:
    """Apply the evidence-grounded verdict ladder and set the opinion-disclaimer flag.

    The ladder is ordered by what the evidence supports, not by severity:
    ``FAIL`` first because a confirmed non-conformity is a conclusion *reached*,
    then ``DISCLAIMER_OF_OPINION`` for the positions where no conclusion could be
    reached at all. Both disclaimer branches set ``opinion_disclaimer``, which is
    what ``report_architect.opinion`` reads — the two used to be derivable
    independently, and F11 is what happened when they disagreed.

    **Fix 25 — the KPI floor was skippable, and skipping it rewarded a worse
    audit.** The floor sat *below* the qualified-pass branch, so it was consulted
    only when every article in the matrix read ``PASS``. Two engagements with the
    same 25% coverage therefore came out:

    ==========================================  ==========================
    matrix                                      verdict
    ==========================================  ==========================
    every article ``PASS``                      ``DISCLAIMER_OF_OPINION``
    one article ``INSUFFICIENT_EVIDENCE``       ``PASS_WITH_OBSERVATIONS``
    ==========================================  ==========================

    The audit that admitted it could not assess something got the *better*
    verdict, because saying so put a token in the matrix that returned before the
    floor was reached. The floor is a statement about the engagement, not about
    one article, so it is now evaluated before any pass-shaped verdict: too
    little delivered is a disclaimer whatever the assessed articles say.

    :param state: The AuditState dict; ``opinion_disclaimer`` is set in place.
    :returns: One of :data:`aaa.platform.state.verdicts.FINAL_VERDICTS`.
    """
    verdicts = set(state.get("compliance_matrix", {}).values())
    phase5_fail = state.get("cgsa_phase5_verdict") == "FAIL"
    csp_fail = state.get("cgsa_csp_satisfiable") is False

    core_insufficient = any(
        v == "INSUFFICIENT_EVIDENCE" and _core_article(a) in _CORE_HIGH_RISK_ARTICLES
        for a, v in state.get("compliance_matrix", {}).items()
    )

    if "FAIL" in verdicts or phase5_fail or csp_fail:
        state["opinion_disclaimer"] = False
        return FAIL

    cs = state.get("completeness_score") or 0.0
    rc = state.get("regulatory_coverage_pct") or 0.0
    ics = state.get("intake_completeness_score") or 0.0
    # Too little of the audit was delivered to stand behind any conclusion. That
    # is an evidence-sufficiency failure, not a non-conformity: this branch used
    # to return FAIL, asserting a breach that was never established.
    delivered_enough = ics >= 0.80 and cs >= 0.75 and rc >= 75.0

    # Cannot conclude conformity on a mandatory high-risk requirement, or could
    # not deliver enough of the audit to conclude at all → disclaimer.
    state["opinion_disclaimer"] = bool(core_insufficient) or not delivered_enough
    if core_insufficient or not delivered_enough:
        return DISCLAIMER_OF_OPINION

    if "INSUFFICIENT_EVIDENCE" in verdicts or "PASS_WITH_OBSERVATIONS" in verdicts:
        return PASS_WITH_OBSERVATIONS

    if ics >= 0.90 and cs >= 0.90 and rc >= 90.0:
        return PASS
    return PASS_WITH_OBSERVATIONS
