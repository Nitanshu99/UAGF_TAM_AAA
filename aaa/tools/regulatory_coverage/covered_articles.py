"""The single definition of "covered" behind KPI 2 and its breakdown.

Both the KPI and the per-article breakdown embedded in T17/T18 used to carry
their own copy of this rule, and both copies counted an article as covered when
its matrix verdict was merely *not* ``PENDING``/``NOT_APPLICABLE`` — which
includes ``INSUFFICIENT_EVIDENCE``. That is finding F13: the headline coverage
read 80% on a run that had assessed two of fourteen articles. One computation
now serves both, so the number and the list explaining it cannot disagree.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aaa.platform.state.verdicts import ASSESSED_ARTICLE_VERDICTS
from aaa.tools.regulatory_coverage.derive_fallback_verdicts import _derive_fallback_verdicts
from aaa.tools.regulatory_coverage.engagement_scope import engagement_articles, scope_is_known

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def covered_articles(state: AuditState) -> dict[str, Any]:
    """Resolve in-scope, covered and missing articles plus the KPI 2 percentage.

    :param state: The AuditState dict. ``compliance_matrix`` is populated with
        any derivable fallback verdicts as a side effect, as it always was.
    :returns: ``{"regulatory_coverage_pct", "in_scope", "covered", "missing",
        "no_obligations_in_scope"}`` — the three article lists sorted, and a flag
        saying the percentage means "nothing binds this system" rather than
        "everything was assessed" (fix 51).
    """
    # Fix 40: the same authority the matrix uses. Reading `_resolve_article_set`
    # alone left the gate-scoped articles (Art. 25, Art. 27, and the five GPAI
    # ids) in the table but outside the denominator — the KPI and the table it
    # explains describing different audits.
    in_scope = engagement_articles(state)
    matrix: dict = _derive_fallback_verdicts(state, in_scope)

    # A requirement that does not bind is not an evidence gap: drop it from both
    # sides of the fraction rather than scoring it as uncovered.
    scope = in_scope - {a for a, v in matrix.items() if v == "NOT_APPLICABLE"}
    covered = {a for a, v in matrix.items()
               if a in scope and v in ASSESSED_ARTICLE_VERDICTS}
    if scope:
        pct = round(100.0 * len(covered) / len(scope), 1)
    else:
        # Fix 51: an empty scope has two very different causes and only one of
        # them is good news. A `minimal`-risk system genuinely carries no
        # mandatory requirements, and 100 % is the true answer — there is nothing
        # to cover. A state whose tier was never established has an empty scope
        # because nobody worked out what binds it, and reporting that as full
        # coverage would let an unscoped engagement pass by having no obligations
        # to fail. Before this fix both read 100 %, and only the second was
        # reachable, because `minimal` still held Art. 50.
        pct = 100.0 if scope_is_known(state) else 0.0
    return {"regulatory_coverage_pct": pct, "in_scope": sorted(scope),
            "covered": sorted(covered), "missing": sorted(scope - covered),
            "no_obligations_in_scope": not scope and scope_is_known(state)}


__all__ = ["covered_articles"]
