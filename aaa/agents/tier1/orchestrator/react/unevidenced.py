"""Close-out honesty for audits that end without running every phase.

``apply_guards`` forces an owed phase when the model *chooses* to close, but a
run whose turn budget runs out never reaches that decision — it drops into
``deterministic_wrapup``, which previously assembled the matrix with no
coverage check at all. A mandatory phase that never ran leaves its articles
unevidenced, and an unevidenced article reports PASS rather than
INSUFFICIENT_EVIDENCE, so the audit closes claiming conformity it never
assessed.

Marking used to be the *only* response, on the reasoning that dispatching after
the budget was exhausted would be an unbounded rescue loop. It is not:
``rescue.run_outstanding`` now forces each owed phase exactly once before this
runs (finding F12), so marking is reserved for what genuinely could not be
produced — a phase with no runner, one already at its dispatch cap, one blocked
by the intake gate, or one whose runner failed. The report should say plainly
which articles were not assessed, and now says it about far fewer of them.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.phases.node_stubs import TEMPLATE_ARTICLES
from aaa.agents.tier1.phases.nodes.plan import PHASE_TO_TEMPLATES
from aaa.tools.regulatory_coverage.ownership import ALWAYS_RUN

logger = logging.getLogger(__name__)


def unevidenced_articles(state: dict[str, Any]) -> list[str]:
    """Articles owned by mandatory phases that produced no artefact.

    :param state: The AuditState dict.
    :type state: dict[str, Any]
    :returns: Sorted article ids with no backing artefact.
    :rtype: list[str]
    """
    plan = state.get("phase_plan") or {}
    produced = set((state.get("phase_artefacts") or {}).keys())
    missing: set[str] = set()
    for phase, status in plan.items():
        # A phase that has not run *yet* has not failed. `deterministic_wrapup`
        # marks before it emits the report, so P6's own templates are always
        # absent at this moment and always produced a moment later — marking them
        # is fix 12's defect one template over: recording as "could not be
        # assessed" work that was never attempted. This was latent until fix 50
        # completed the article map and T17/T18 gained the entries that exposed it.
        if str(status).upper() != "M" or phase in ALWAYS_RUN:
            continue
        for tid in PHASE_TO_TEMPLATES.get(phase, []):
            if tid not in produced:
                missing.update(TEMPLATE_ARTICLES.get(tid, []))
    return sorted(missing)


def mark_unevidenced(state: dict[str, Any]) -> list[str]:
    """Record unevidenced articles so the matrix cannot report them PASS.

    :param state: The AuditState dict, mutated in place.
    :type state: dict[str, Any]
    :returns: The articles newly marked insufficient.
    :rtype: list[str]
    """
    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    newly = [a for a in unevidenced_articles(state) if a not in recorded]
    recorded.extend(newly)
    if newly:
        logger.warning(
            "Closing without running every mandatory phase; %d article(s) marked "
            "INSUFFICIENT_EVIDENCE rather than PASS: %s", len(newly), ", ".join(newly))
    return newly
