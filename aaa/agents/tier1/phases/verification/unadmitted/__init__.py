"""Finding Q1 — an artefact the Verifier did not admit takes its articles with it.

Fix 20 built this gate for one verdict and wired it to that verdict alone.  Its
own words say why the gate has to exist: ``_derive_verdicts`` builds the matrix
from the union of admitted, insufficient, finding-bearing and gate-scoped
articles, so *"an article admitted by nothing else simply stops being listed —
and an article that is not in the matrix is not in the coverage denominator
either.  Silence is the one answer worse than accept."*

Nothing in that reasoning is specific to ``unverified``.  Three verdicts leave an
artefact outside :data:`~aaa.platform.state.admission.ADMITTED_VERDICTS`:
``unverified`` says the check never ran, ``rerun`` and ``escalate_hitl`` say it
ran and rejected the artefact.  All three put the artefact in none of the four
sets, and the post-fix part-2 run delivered the consequence: Art. 12, Art. 43 and
Art. 72 were in scope, each was the sole responsibility of an artefact the
Verifier escalated, and none of them appears in the client's article-by-article
conformity table at all — not as ``INSUFFICIENT_EVIDENCE``, absent.

So the gate asks the admission question rather than naming a verdict: *did the
Verifier admit this artefact?*  That is the one question
:mod:`aaa.platform.state.admission` exists to answer, and asking it here keeps
this gate from drifting away from the matrix, the T18 manifest and the two KPI
tools when a verdict is added.

The articles are recorded ``INSUFFICIENT_EVIDENCE``, which is the verdict this
system already uses for *we could not obtain sufficient appropriate evidence* —
the same route fix 7 gives a phase that closes below the confidence floor and
fix 15 gives an article whose tools produced nothing.  The difference is only in
which link of the chain failed: the agent's confidence, the tools beneath it, or
the independent check above it.

Report templates are excluded from the article half for the reason
``gate_on_confidence`` excludes them: T17 and T18 summarise a state that has
already been assessed, so an unadmitted write-up says nothing about the evidence
underneath it.  They are *not* excluded from the HITL flag or the finding — the
post-fix run's two delivered documents were exactly the artefacts whose critique
did not run, and a reader has to be told that.

The gate is idempotent and two-way.  It rewrites its own record of the phase each
time the phase runs, because the Orchestrator can re-dispatch a whole phase (Q8)
and an artefact escalated on dispatch 1 and admitted on dispatch 2 must not leave
a stale insufficiency behind — the same property the rerun loop already relies on
one level down.
"""
from __future__ import annotations

import logging

from aaa.agents.tier1.phases.verification.unadmitted.finding import _record_finding
from aaa.agents.tier1.phases.verification.unadmitted.records import (
    UNADMITTED_VERDICTS,
    _entry,
    _is_phase_entry,
    _reason,
    clear_phase_finding,
)
from aaa.agents.tier1.phases.verification.unadmitted.release import clear_unadmitted_insufficiency
from aaa.agents.tier1.phases.verification.unadmitted.rewrite import rewrite_phase_records
from aaa.platform.state.admission import artefact_verdict

logger = logging.getLogger(__name__)


def gate_on_unadmitted(state: dict, tid_articles: dict[str, list[str]], *,
                       phase_id: str, phase_label: str) -> list[str]:
    """Record the articles of an artefact the Verifier did not admit as unevidenced.

    Read after the rerun loop closes, from the critiques as they finally stand:
    an artefact escalated on attempt 1 and admitted on attempt 2 is admitted, and
    must not leave a stale insufficiency behind.

    :param state: The mutable AuditState dict.
    :param tid_articles: Template ids this phase emitted, mapped to the articles
        each one evidences.
    :param phase_id: Dispatch phase id (``P2``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :returns: The articles newly marked insufficient by this call.
    """
    unadmitted, articles = rewrite_phase_records(
        state, tid_articles, phase_id=phase_id, phase_label=phase_label)
    if unadmitted is None:
        return []
    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    newly = [a for a in articles if a not in recorded]
    recorded.extend(newly)
    _record_finding(state, unadmitted, articles, phase_id=phase_id, phase_label=phase_label)
    logger.warning(
        "%s: %d artefact(s) not admitted (%s) — %d article(s) recorded "
        "INSUFFICIENT_EVIDENCE rather than assessed: %s",
        phase_label, len(unadmitted),
        ", ".join(f"{t} ({artefact_verdict(state, t)})" for t in unadmitted) or "none",
        len(newly), ", ".join(newly) or "none new")
    return newly


__all__ = ["UNADMITTED_VERDICTS", "_entry", "_is_phase_entry", "_reason",
           "clear_phase_finding", "clear_unadmitted_insufficiency", "gate_on_unadmitted"]
