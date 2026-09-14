"""An in-scope article nothing can evidence is listed, not omitted — fix 41 (R9).

RetailIQ carries three obligations and the delivered table had **two rows**. Art. 50
was in KPI 2's denominator — the coverage of 33.3 % is 1 of 3 — and in no row of the
conformity table the client actually reads. The number knew; the table did not say.

That is the same rule fix 20 stated one gate over and fix 26 generalised: *silence is
the one answer worse than accept*. An article absent from the matrix is absent from
the reader's view of what was and was not assessed, and absence reads as "not
applicable to us" rather than as "nobody looked".

So the matrix is seeded from the engagement's own scope. Every article that binds the
client appears; one nothing evidenced falls through ``_article_verdict``'s last
branch to ``INSUFFICIENT_EVIDENCE``, which is the verdict this system already has for
*we could not obtain sufficient appropriate evidence*. And where the cause is
structural rather than circumstantial — no artefact in the catalogue evidences this
article, or none that this engagement's plan will run — the finding says so, because
"the audit did not reach it" and "the audit cannot reach it" are different facts and
only one of them is fixable by re-running.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.compliance_matrix.logger import logger
from aaa.agents.tier1.phases.compliance_matrix.unassessable.reasons import unassessable_reasons
from aaa.tools.findings import make_finding
from aaa.tools.regulatory_coverage.engagement_scope import (
    canonical_article,
    core_article,
    engagement_articles,
    scope_is_known,
)

UNASSESSABLE_FINDING_ID = "ORCH-ARTICLE-UNASSESSABLE"


def scope_seed(state: dict, produced: set[str] | None = None) -> set[str]:
    """Every article that binds this engagement and is not already accounted for.

    *produced* is what the audit actually built a row for. An article already
    present under another spelling is **not** seeded again: case 04 carries
    ``Art.51``-``Art.55`` where ``ARTICLE_SET`` says ``GPAI_51``-``GPAI_55``
    (finding R17), and seeding the canonical ids beside them would list the same
    five obligations twice with opposite verdicts — a defect, not a disclosure.

    :param state: The AuditState dict.
    :param produced: Articles the audit already has a row for.
    :returns: The in-scope articles still unaccounted for, or an empty set when no
        tier is stated — the same reading fix 40 gives an unknown scope: it
        narrows nothing, and it invents nothing either.
    """
    if not scope_is_known(state):
        return set()
    seen = {canonical_article(core_article(a)) for a in (produced or set())}
    return {a for a in engagement_articles(state)
            if canonical_article(core_article(a)) not in seen}


def record_unassessable(state: dict, matrix: dict[str, str]) -> list[str]:
    """Raise one finding for the in-scope articles this audit could never reach.

    :param state: The mutable AuditState dict.
    :param matrix: The compliance matrix as just derived.
    :returns: The unassessable articles, sorted.
    """
    findings: list[dict[str, Any]] = state.setdefault("blocking_findings", [])
    findings[:] = [f for f in findings if f.get("finding_id") != UNASSESSABLE_FINDING_ID]
    reasons = {a: why for a, why in unassessable_reasons(state).items()
               if matrix.get(a) == "INSUFFICIENT_EVIDENCE"}
    if not reasons:
        return []

    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    recorded.extend(a for a in reasons if a not in recorded)
    findings.append(make_finding(
        finding_id=UNASSESSABLE_FINDING_ID,
        description=(
            "The following articles bind this engagement and no artefact this audit "
            "produces can evidence them, so they are unassessed for a structural "
            "reason rather than a circumstantial one — re-running the audit will not "
            "change them: "
            + "; ".join(f"{a} ({why})" for a, why in reasons.items())),
        materiality="possibly_material",
        articles=sorted(reasons),
        source_phase="ORCH",
        recommendation=("Obtain evidence for these articles outside this pipeline, or "
                        "record why they do not bind, before the report is signed."),
    ))
    logger.warning(
        "%d in-scope article(s) cannot be evidenced by any artefact this audit "
        "produces: %s", len(reasons), ", ".join(sorted(reasons)))
    return sorted(reasons)


__all__ = ["UNASSESSABLE_FINDING_ID", "record_unassessable", "scope_seed"]
