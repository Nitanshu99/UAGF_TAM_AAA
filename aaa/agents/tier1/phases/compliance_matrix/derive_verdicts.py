"""Derive every article verdict and its traceability entry from the evidence on the state."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry
from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import _findings_by_article
from aaa.agents.tier1.phases.compliance_matrix.out_of_scope_findings import (
    restate_out_of_scope_findings,
)
from aaa.agents.tier1.phases.compliance_matrix.partner_verdicts import apply_partner_verdicts
from aaa.agents.tier1.phases.compliance_matrix.scope_articles import (
    record_scoped_unevidenced,
    scope_gate_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.skipped_phases import record_skipped_phases
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import _article_verdict
from aaa.agents.tier1.phases.compliance_matrix.unassessable import record_unassessable, scope_seed
from aaa.platform.audit_programme import apply_audit_programme
from aaa.tools.regulatory_coverage.engagement_scope import keep_in_scope


def _derive_verdicts(state: dict) -> None:
    """Populate ``compliance_matrix`` + ``article_evidence`` from evidence."""
    admitted = _collect_admitted_articles(state)
    # Procedures not performed become scope limitations, and unevidence an article
    # only where no sufficient procedure covered it (audit programme).
    apply_audit_programme(state)
    restate_out_of_scope_findings(state)
    insufficient = set(state.get("insufficient_evidence_articles", []) or [])
    fba = _findings_by_article(state)

    # A gate-scoped article must reach the matrix even though nothing admits it:
    # an article absent from the matrix is absent from the coverage denominator
    # too, which is the trap fix 20 documented one gate over.
    scoped = scope_gate_articles(state)
    # Fix 40 (R8): the four sets are built from `_TEMPLATE_ARTICLES` and the phase
    # runners' `tid_articles`, constants written when every engagement was
    # high-risk. This is the one place all four meet, so it is where the
    # engagement's own scope is applied — a limited-risk client's table used to
    # carry eleven articles that do not bind it, one of them PASS.
    # Fix 41 (R9): the four sets are what the audit *produced*, and an article
    # nothing produced was simply absent — RetailIQ's Art. 50 was in KPI 2's
    # denominator and in no row of the table the client reads. Seeding from the
    # engagement's own scope means every article that binds it appears, and one
    # nothing evidenced falls to INSUFFICIENT_EVIDENCE rather than to silence.
    produced = set(admitted) | set(insufficient) | set(fba.keys()) | set(scoped)
    all_articles = keep_in_scope(
        state, sorted(produced | scope_seed(state, produced)),
        claimed_by="compliance matrix")
    # Preserve any verdicts already set deterministically (e.g., scope gate FAILs).
    preset = {a: v for a, v in state.get("compliance_matrix", {}).items()
              if v not in (None, "PENDING")}

    # Fix 43: two passes. A row's rationale may need to name a sibling row's
    # verdict — `Art.15` FAIL beside `Art.15§1` PASS_WITH_OBSERVATIONS is a pair a
    # regulator cannot read without one — so every verdict is decided before any
    # rationale is written, rather than relying on `sorted()` happening to put a
    # parent before its paragraphs.
    matrix: dict[str, str] = {
        article: preset.get(article) or _article_verdict(
            article, fba.get(article, []), admitted, insufficient)
        for article in sorted(set(all_articles))}
    evidence: dict[str, dict] = {
        article: _evidence_entry(state, article, verdict, fba.get(article, []), matrix)
        for article, verdict in matrix.items()}

    # Partner (S6/S7) evidence can only worsen its own article — never
    # upgrade one, and never touch an article outside its contractual scope.
    for article in apply_partner_verdicts(state, matrix):
        art_findings = fba.get(article, [])
        evidence[article] = _evidence_entry(
            state, article, matrix[article], art_findings, matrix)
        evidence[article]["rationale"] += " Downgraded by independent partner evidence."

    state["compliance_matrix"] = matrix
    state["article_evidence"] = evidence
    record_scoped_unevidenced(state, matrix)
    # "The audit did not reach it" and "the audit cannot reach it" are different
    # facts, and only one is fixable by re-running.
    record_unassessable(state, matrix)
    # And "the audit was never asked to reach it" is a third — the phase plan
    # skipped it from the declaration, before any phase dispatched.
    record_skipped_phases(state)


__all__ = ["_derive_verdicts"]
