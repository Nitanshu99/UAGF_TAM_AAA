"""A phase that delivered nothing must say so — fix 35 (findings R2 and R3).

When a phase agent produced no report, ``run_phase_with_verification`` returned
``(None, state)`` *before* ``_verify_artefacts`` and *before*
``gate_on_unadmitted``, and the phase runner then called its deterministic stub.
In [case 01] the ScopeAgent's 216.8 s reply was discarded by a 120 s budget and
``node_phase1_stub`` wrote T02–T05 in its place — each with a synthetic
``mem://`` URI, each carrying a manufactured ``accept_with_notes`` critique,
which is an **admitting** verdict. So the run delivered four artefacts that
pointed at nothing, were admitted by a critique no Verifier wrote, and **no
finding recorded why** (R2).

That silence is what made R3 undetectable. ``phase_has_run("P1")`` asks whether
``T02_system_card`` is in ``phase_artefacts``; the stub had put it there; so the
Orchestrator's precedence guard saw a phase that had run, and the model's
*"Phase 1 completed successfully with T02_system_card produced"* could not be
contradicted by the very envelope that said ``produced: false``.

**Which option, and why.** The backlog offered two: withhold the stub, or keep it
and gate it. Only withholding can satisfy the acceptance criterion *"`phase_has_run`
and the precedence guard agree with reality"* — a gated stub is still an artefact,
and ``phase_has_run`` would still answer yes to a phase that produced nothing. So
the stub goes from the failure path, and this module supplies what it was
pretending to be: the phase's articles recorded ``INSUFFICIENT_EVIDENCE`` and a
finding that names the phase, what it cost, and why it stopped.

The stub keeps its real job. ``node_phase1_stub`` and its siblings still run when
the agent is **not wired** — a dev or offline configuration where no dispatch was
ever attempted and a deterministic placeholder is an honest answer. A phase that
was wired, dispatched and failed is a different fact, and used to be recorded as
the same one.

**The finding says which failure it was**, because three findings produce this one
symptom and a reader has to be able to tell them apart: a phase abandoned at its
budget is R1's, a provider failure is R7's, and a client-ceiling timeout is R6's.
The evidence for that distinction is already in hand at the moment of failure —
``run_agent_on_state`` catches the exception — so it is carried here rather than
inferred later from a latency.
"""
from __future__ import annotations

import logging

from aaa.agents.tier1.phases.verification.no_report.failure import (
    FAILURE_KEY,
    NO_REPORT,
    _cause,
    _classify,
    _entries,
    record_phase_failure,
)
from aaa.agents.tier1.phases.verification.no_report.finding import _record_finding
from aaa.tools.regulatory_coverage.engagement_scope import keep_in_scope

logger = logging.getLogger(__name__)


def gate_on_no_report(state: dict, tid_articles: dict[str, list[str]], *,
                      phase_id: str, phase_label: str) -> list[str]:
    """Record a phase that produced nothing, and hold its articles back.

    Writes into ``unadmitted_artefacts`` beside the real unadmitted verdicts, so
    a re-dispatch that *does* deliver clears these entries and releases their
    articles through the machinery :func:`~.unadmitted.gate_on_unadmitted`
    already owns — the two-way property Q8 established, which matters here
    because the Orchestrator re-dispatched three lost phases in case 01 alone.

    :param state: The mutable AuditState dict.
    :param tid_articles: Template ids this phase was contracted to emit, mapped
        to the articles each one would have evidenced.
    :param phase_id: Dispatch phase id (``P1``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :returns: The articles newly recorded ``INSUFFICIENT_EVIDENCE``.
    """
    from aaa.agents.tier1.phases.verification.unadmitted import _is_phase_entry

    failure = state.pop(FAILURE_KEY, None) or {}
    mine = _entries(tid_articles, failure, phase_id=phase_id, phase_label=phase_label)
    kept = [e for e in (state.get("unadmitted_artefacts") or [])
            if not _is_phase_entry(e, phase_id, set(tid_articles))]
    state["unadmitted_artefacts"] = kept + mine

    # Fix 40 (R8): same authority as the matrix and the other two gates.
    articles = keep_in_scope(state, sorted({a for e in mine for a in e["articles"]}),
                             claimed_by=phase_label)
    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    newly = [a for a in articles if a not in recorded]
    recorded.extend(newly)

    _record_finding(state, list(tid_articles), articles, failure,
                    phase_id=phase_id, phase_label=phase_label)
    state["hitl_required"] = True
    logger.warning(
        "%s: produced no report — %s. %d artefact(s) withheld (%s) and %d "
        "article(s) recorded INSUFFICIENT_EVIDENCE: %s",
        phase_label, _cause(failure), len(tid_articles), ", ".join(tid_articles),
        len(newly), ", ".join(newly) or "none new")
    return newly


__all__ = ["FAILURE_KEY", "NO_REPORT", "_classify", "gate_on_no_report",
           "record_phase_failure"]
