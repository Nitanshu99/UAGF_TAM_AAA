"""Articles the Stage A scope gate brings into scope — which it does not evidence.

``_collect_admitted_articles`` read four scope-gate flags and put their articles
in the *admitted* set.  ``_article_verdict`` reads that set as "admitted,
verifier-accepted, no findings" and answers ``PASS``, so a flag produced a passed
article on zero evidence.

The gate's own reasoning says what the flags mean: *"entity assumes provider
obligations"*, *"Art. 55 obligations apply"*, *"Art. 50 transparency
obligation(s) triggered"*.  Every one says an obligation **applies**; none says
it is met.  This is the same false PASS fix 21 took out of the evidence list, one
link further up — where it reaches the verdict rather than the rationale, and
where fix 21 could only make it visible by leaving the basis empty.

The flags are unchanged.  What changes is which set they feed: an in-scope
article with no admitted evidence falls to ``_article_verdict``'s own last
branch, ``INSUFFICIENT_EVIDENCE``, which is the verdict this system already has
for "we could not obtain sufficient appropriate evidence".
"""
from __future__ import annotations

from typing import Any, Final

from aaa.agents.tier1.phases.compliance_matrix.logger import logger
from aaa.tools.findings import make_finding

# Fix 40 moved the pure lookup down to the layer KPI 2's article set lives in, so
# one module can answer "what binds this engagement?". Re-exported here because
# every existing import names this module.
from aaa.tools.regulatory_coverage.gate_articles import (  # noqa: F401
    GATE_ARTICLES,
    scope_gate_articles,
)

SCOPE_FINDING_ID: Final = "ORCH-SCOPE-UNEVIDENCED"


def record_scoped_unevidenced(state: dict, matrix: dict[str, str]) -> list[str]:
    """Record gate-scoped articles that no admitted artefact evidenced.

    Writing them to ``insufficient_evidence_articles`` is what makes the result
    idempotent: the finding this also raises is ``possibly_material``, and on a
    second pass ``_article_verdict`` would otherwise read it as a qualification
    and answer ``PASS_WITH_OBSERVATIONS``.  The insufficiency outranks it.

    :param state: The mutable AuditState dict.
    :param matrix: The compliance matrix as just derived.
    :returns: The gate-scoped articles left unevidenced, sorted.
    """
    scoped = scope_gate_articles(state)
    unevidenced = sorted(a for a in scoped if matrix.get(a) == "INSUFFICIENT_EVIDENCE")
    if not unevidenced:
        return []

    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    recorded.extend(a for a in unevidenced if a not in recorded)

    findings: list[dict[str, Any]] = state.setdefault("blocking_findings", [])
    if not any(f.get("finding_id") == SCOPE_FINDING_ID for f in findings):
        flags = sorted({scoped[a] for a in unevidenced})
        findings.append(make_finding(
            finding_id=SCOPE_FINDING_ID,
            description=(
                f"The Stage A scope gate brought {', '.join(unevidenced)} into scope "
                f"({', '.join(flags)}), and no admitted artefact evidences them. The "
                f"flag records that the obligation applies, not that it is met."),
            materiality="possibly_material",
            articles=unevidenced,
            source_phase="ORCH",
            recommendation=("Assess these articles, or record why they do not bind, "
                            "before the report is signed."),
        ))
    logger.warning(
        "Scope gate brought %d article(s) into scope that nothing evidenced: %s",
        len(unevidenced), ", ".join(unevidenced))
    return unevidenced


__all__ = ["GATE_ARTICLES", "SCOPE_FINDING_ID", "scope_gate_articles",
           "record_scoped_unevidenced"]
